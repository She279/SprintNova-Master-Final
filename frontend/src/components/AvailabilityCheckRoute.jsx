import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { weeklyAvailabilityApi } from "../api/weekly-availability";
import { AvailabilitySetupModal } from "./AvailabilitySetupModal";
import { useWorkSession } from "../context/WorkSessionContext";

/**
 * Wrapper component that checks if user has configured availability.
 * Shows modal if not configured.
 *
 * Usage: wrap your protected routes with this component
 */
export function AvailabilityCheckRoute({ children }) {
  const { session } = useAuth();
  const [isAvailable, setIsAvailable] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { startSession } = useWorkSession();

  useEffect(() => {
    const checkAvailability = async () => {
      if (!session) return;

      // Don't require availability setup for clients
      if (session.role === "client" || session.role === "owner_admin") {
        setIsLoading(false);
        return;
      }

      try {
        const result = await weeklyAvailabilityApi.isConfigured();
        if (!result.is_configured) {
          setShowModal(true);
          setIsAvailable(false);
        } else {
          setIsAvailable(true);
        }
      } catch (error) {
        console.error("Failed to check availability:", error);
        // Allow access even if check fails
        setIsAvailable(true);
      } finally {
        setIsLoading(false);
      }
    };

    checkAvailability();
  }, [session]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {children}
      <AvailabilitySetupModal
        isOpen={showModal}
        onClose={() => {
          // Don't allow closing without setup for non-clients
          if (session?.role !== "client") return;
          setShowModal(false);
        }}
        onSuccess={() => {
          setIsAvailable(true);
          setShowModal(false);
          if (session?.role !== "client" && session?.role !== "owner_admin") startSession().catch(() => {});
        }}
      />
    </>
  );
}
