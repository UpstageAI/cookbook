export async function getStandardizedNote(payload: {
  patientId: string;
  procedureId: string;
  note: string;
}) {
  const response = await fetch(
    "https://rad-rag-backend-2.onrender.com/api/standardize",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error("API 요청 실패");
  }
  console.log(response.json);
  return response.json();
}
