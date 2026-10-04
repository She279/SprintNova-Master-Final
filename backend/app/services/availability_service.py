from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.availability import Availability, AvailabilityStatus
from app.models.user import User
from app.schemas.availability import (
    AvailabilitySetRequest,
    TeamAvailabilityDay,
    WeeklyAvailabilitySetupRequest,
)


def set_availability(
    db: Session,
    user_id: int,
    payload: AvailabilitySetRequest,
) -> Availability:
    """Upsert: one availability record per (user, date)."""

    record = (
        db.query(Availability)
        .filter(
            Availability.user_id == user_id,
            Availability.date == payload.date,
        )
        .first()
    )

    if record:
        record.status = payload.status
        record.hours_available = payload.hours_available
        record.note = payload.note
    else:
        record = Availability(
            user_id=user_id,
            **payload.model_dump(),
        )
        db.add(record)

    db.commit()
    db.refresh(record)

    return record


def list_own_availability(
    db: Session,
    user_id: int,
    start: date,
    end: date,
) -> list[Availability]:

    return (
        db.query(Availability)
        .filter(
            Availability.user_id == user_id,
            Availability.date >= start,
            Availability.date <= end,
        )
        .order_by(Availability.date)
        .all()
    )


def team_availability(
    db: Session,
    user_ids: list[int],
    start: date,
    end: date,
) -> list[TeamAvailabilityDay]:

    if not user_ids:
        return []

    rows = (
        db.query(Availability, User)
        .join(User, Availability.user_id == User.id)
        .filter(
            Availability.user_id.in_(user_ids),
            Availability.date >= start,
            Availability.date <= end,
        )
        .order_by(Availability.date)
        .all()
    )

    return [
        TeamAvailabilityDay(
            date=a.date,
            user_id=a.user_id,
            full_name=f"{u.first_name} {u.last_name}",
            status=a.status,
            hours_available=a.hours_available,
        )
        for a, u in rows
    ]


def setup_weekly_availability(
    db: Session,
    user_id: int,
    payload: WeeklyAvailabilitySetupRequest,
) -> list[Availability]:
    """
    Save the employee's weekly working schedule for the next 7 days.

    Existing availability records are updated instead of duplicated.
    """

    day_map = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday",
    }

    today = date.today()
    results = []

    for offset in range(7):
        current_date = today + timedelta(days=offset)
        day_name = day_map[current_date.weekday()]

        day_schedule = payload.schedule.get(day_name)

        start_time = None
        end_time = None

        if day_schedule:
            start_time = day_schedule.start_time
            end_time = day_schedule.end_time

        # Working day
        if start_time and end_time:

            try:
                start = datetime.strptime(start_time, "%H:%M")
                end = datetime.strptime(end_time, "%H:%M")
            except ValueError:
                raise ValueError(
                    f"Invalid time format for {day_name}. "
                    "Use HH:MM format."
                )

            hours = (end - start).total_seconds() / 3600

            if hours <= 0:
                raise ValueError(
                    f"End time must be after start time for {day_name}."
                )

            status = AvailabilityStatus.AVAILABLE

        # Day off
        else:
            hours = 0
            status = AvailabilityStatus.UNAVAILABLE

        # Find existing record
        record = (
            db.query(Availability)
            .filter(
                Availability.user_id == user_id,
                Availability.date == current_date,
            )
            .first()
        )

        # Update existing record
        if record:
            record.status = status
            record.hours_available = hours
            record.note = f"Weekly schedule ({payload.timezone})"

        # Create new record
        else:
            record = Availability(
                user_id=user_id,
                date=current_date,
                status=status,
                hours_available=hours,
                note=f"Weekly schedule ({payload.timezone})",
            )

            db.add(record)

        results.append(record)

    db.commit()

    for record in results:
        db.refresh(record)

    return results