export default function Spinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-white"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-40"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path
        className="opacity-100"
        fill="currentColor"
        d="M12 2a10 10 0 0 1 10 10h-2.5a7.5 7.5 0 0 0-7.5-7.5V2z"
      />
    </svg>
  );
}
