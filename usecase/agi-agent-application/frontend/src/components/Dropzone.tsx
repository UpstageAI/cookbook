import { useRef } from "react";
import uploadIcon from "../assets/upload.svg";

interface DropzoneProps {
  selectedFile: File | null;
  onFileSelect: (file: File) => void;
  onSubmit: () => void;
  uploadStatus: string;
}

export default function Dropzone({
  selectedFile,
  onFileSelect,
  onSubmit,
  uploadStatus,
}: DropzoneProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      onFileSelect(e.target.files[0]);
      e.target.value = "";
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) onFileSelect(files[0]);
  };

  const handleClick = () => {
    if (!selectedFile) fileInputRef.current?.click();
  };

  const getMessageColor = () => {
    if (!uploadStatus) return "";
    if (
      uploadStatus.toLowerCase().includes("fail") ||
      uploadStatus.toLowerCase().includes("only")
    ) {
      return "#FF6767";
    }
    return "#3FA780";
  };

  return (
    <div
      id="dropZone"
      className="w-[90%] max-w-[600px] min-h-[440px] border-2 border-dashed border-black rounded-md flex flex-col justify-center items-center text-center px-4 py-6 mx-auto transition"
      onClick={handleClick}
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      <input
        key={selectedFile?.name || "input-key"}
        ref={fileInputRef}
        type="file"
        accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/pdf, image/png, image/jpeg"
        hidden
        onChange={handleFileChange}
      />

      {!selectedFile && (
        <>
          <img
            src={uploadIcon}
            alt="Upload"
            className="w-[60px] h-[60px] mb-4"
          />
          <p className="text-lg font-semibold text-black mb-2">
            Upload File (csv, pdf, xlsx, jpeg, png)
          </p>
          <button
            className="mt-4 px-4 py-2 text-black border border-black rounded-md font-medium hover:bg-[#E4E4E8]"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse File
          </button>
        </>
      )}

      {/* 상태 메시지 + Go 버튼 */}
      <div
        className="mt-4 text-sm text-center max-w-[90%] break-words"
        style={{ color: getMessageColor() }}
      >
        {uploadStatus && <p>{uploadStatus}</p>}
        {selectedFile &&
          uploadStatus.toLowerCase().includes("successfully") && (
            <button
              id="submitBtn"
              className="mt-4 px-4 py-2 text-white rounded-lg font-semibold hover:bg-blue-600 transition"
              style={{ backgroundColor: "#678AFF" }}
              onClick={(e) => {
                e.stopPropagation();
                onSubmit();
              }}
            >
              Go!
            </button>
          )}
      </div>
    </div>
  );
}
