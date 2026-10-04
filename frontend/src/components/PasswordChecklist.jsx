import { checkPasswordStrength } from "../utils/password";

export function PasswordChecklist({ password }) {
  const rules = checkPasswordStrength(password);
  return (
    <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 mt-1">
      {rules.map((r) => (
        <li
          key={r.key}
          className={`flex items-center gap-1.5 text-xs transition-colors ${
            r.passed ? "text-success" : "text-muted"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${r.passed ? "bg-success" : "bg-line"}`} />
          {r.label}
        </li>
      ))}
    </ul>
  );
}
