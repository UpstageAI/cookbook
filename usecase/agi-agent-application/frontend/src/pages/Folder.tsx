import { useState } from "react";
import resetIcon from "../assets/refreshIcon.svg";
import Dropzone from "../components/Dropzone";

export default function Folder() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>("");
  const [result, setResult] = useState<any>(null);

  const handleUploadPrepare = (file: File) => {
    const allowedTypes = [
      "text/csv",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
      "application/pdf",
      "image/png",
      "image/jpeg",
    ];

    if (!allowedTypes.includes(file.type)) {
      setUploadStatus("Only CSV, XLSX, PDF, or image files are allowed.");
      return;
    }

    setSelectedFile(file);
    setUploadStatus(`"${file.name}" uploaded successfully.`);
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    setUploadStatus(`Uploading "${selectedFile.name}"...`);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("/extract", {
        method: "POST",
        body: formData,
      });
      const result = await res.json();
      setResult(result);
    } catch (err) {
      setUploadStatus("Failed to request server.");
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setUploadStatus("");
    setResult(null);
  };

  return (
    <main
      className="max-w-[1000px] mx-auto px-4 py-10 font-pretendard"
      style={{ color: "#26262C" }}
    >
      {/* header */}
      <div className="flex items-center justify-between gap-3 mb-4 w-full max-w-[600px] mx-auto">
        <h1 className="text-xl font-bold text-left">
          Standardize Your File Dummies
        </h1>
        <img
          src={resetIcon}
          alt="Reset"
          className="w-8 h-8 cursor-pointer"
          onClick={handleReset}
        />
      </div>

      {/* 결과 or 업로드 박스 */}
      {result ? (
        <div
          className="w-[90%] max-w-[600px] mx-auto min-h-[440px] rounded-xl p-6 border text-sm leading-relaxed"
          style={{
            backgroundColor: "#EFEFF1",
            borderColor: "#CECDD5",
            color: "#6B6A7B",
          }}
        >
          <h2 className="text-lg font-semibold mb-4">Extracted Result</h2>
          <pre className="whitespace-pre-wrap break-words">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      ) : (
        <Dropzone
          selectedFile={selectedFile}
          onFileSelect={handleUploadPrepare}
          onSubmit={handleSubmit}
          uploadStatus={uploadStatus}
        />
      )}
    </main>
  );
}
