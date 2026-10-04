export function checkPasswordStrength(password) {
  const rules = [
    { key: "length", label: "At least 8 characters", test: (p) => p.length >= 8 },
    { key: "upper", label: "An uppercase letter", test: (p) => /[A-Z]/.test(p) },
    { key: "lower", label: "A lowercase letter", test: (p) => /[a-z]/.test(p) },
    { key: "digit", label: "A number", test: (p) => /[0-9]/.test(p) },
    { key: "special", label: "A special character", test: (p) => /[^A-Za-z0-9]/.test(p) },
  ];
  return rules.map((r) => ({ ...r, passed: r.test(password) }));
}

export function isPasswordValid(password) {
  return checkPasswordStrength(password).every((r) => r.passed);
}
