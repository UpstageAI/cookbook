export function CTAButton({ name }: { name: string }) {
  return (
    <div className="px-6 py-3 bg-blue-500 text-white rounded-md text-body1 hover:bg-blue-400 font-semibold">
      {name}
    </div>
  );
}
