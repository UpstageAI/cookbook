import { useState } from "react";
import { getStandardizedNote } from "../api/standardize";
import xrayImage from "../assets/x-ray.png";
import Spinner from "../components/Loading";

const mockPatients = ["12334", "45678", "98765"];
const mockProcedures = ["0001.dcm", "0002.dcm", "0003.dcm"];

interface StandardizedRow {
  Hierarchy: string;
  "Input Description": string;
  "Concept Name": string;
  "Concept ID": string;
}

export default function Playground() {
  const [selectedPatient, setSelectedPatient] = useState(mockPatients[0]);
  const [selectedProcedure, setSelectedProcedure] = useState(mockProcedures[0]);
  const [clinicalNote, setClinicalNote] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [standardizedResults, setStandardizedResults] = useState<
    StandardizedRow[]
  >([]);

  const handleStandardize = async () => {
    setIsLoading(true);
    try {
      const result = await getStandardizedNote({
        patientId: selectedPatient,
        procedureId: selectedProcedure,
        note: clinicalNote,
      });
      console.log(result);
      setStandardizedResults(result); // standardization results
    } catch (error) {
      setStandardizedResults([]); // failure -> reset
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearInputText = () => {
    setStandardizedResults([]); // reset
    setClinicalNote("");
  };

  const handleFindTag = () => {
    alert("DICOM viewer feature is under development.");
  };

  return (
    <div className="max-w-screen-xl mx-auto p-8 space-y-8 flex flex-col items-center">
      <div className="flex-col w-[90%]">
        <label className="block mb-3 font-semibold text-[#26262C] text-xl">
          Patient
        </label>
        <div className="flex gap-8">
          <select
            value={selectedPatient}
            onChange={(e) => setSelectedPatient(e.target.value)}
            className="w-40 px-2 h-10 rounded-lg shadow-[0_2px_8px_rgba(0,0,0,0.12)] border-none"
          >
            {mockPatients.map((patient) => (
              <option key={patient} value={patient}>
                {patient}
              </option>
            ))}
          </select>
          <div className="flex flex-col bg-white rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.12)] w-100 justify-center px-8 py-6">
            <h2 className="font-semibold mb-4" style={{ color: "#26262C" }}>
              Patient Information
            </h2>
            <ul className="text-sm space-y-1">
              <li className="flex text-[#474653] justify-between">
                <strong>Name</strong> Lola Greenwood
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>Patient ID</strong> 12334
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>Gender</strong> female
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>Nationality</strong> USA
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>Pay Type</strong> IP
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>Insurance ID</strong> 2123767
              </li>
            </ul>
          </div>
          <div className="flex flex-col bg-white rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.12)] w-100 justify-center px-8 py-6">
            <h2 className="font-semibold mb-4" style={{ color: "#26262C" }}>
              Medical History
            </h2>
            <ul className="text-sm space-y-1">
              <li className="flex text-[#474653] justify-between">
                <strong>2025.02.03</strong> Active Lung Lesion
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>2025.01.01</strong> Normal
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>2025.01.01</strong> Chest-Xray
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>2024.09.03</strong> Healed TB
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>2024.09.03</strong> Chest-Xray
              </li>
              <li className="flex text-[#474653] justify-between">
                <strong>2023.02.01</strong> RMP
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex-col w-[90%]">
        <label className="block mb-3 font-semibold text-[#26262C] text-xl">
          Procedures
        </label>
        <div className="flex gap-8">
          <select
            value={selectedProcedure}
            onChange={(e) => setSelectedProcedure(e.target.value)}
            className="w-40 px-2 h-10 rounded-lg shadow-[0_2px_8px_rgba(0,0,0,0.12)] border-none"
            style={{ borderColor: "#ADACB9" }}
          >
            {mockProcedures.map((proc) => (
              <option key={proc} value={proc}>
                {proc}
              </option>
            ))}
          </select>
          <div className="flex flex-col bg-white shadow-[0_2px_8px_rgba(0,0,0,0.12)] w-100 justify-center px-8 py-6">
            <img src={xrayImage} alt="X-ray" className="object-cover w-80" />
          </div>
          <div className="flex flex-col bg-white rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.12)] w-100 justify-center px-8 py-6">
            <h2 className="font-semibold mb-4 text-[#26262C]">
              DICOM Metadata
            </h2>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ color: "#6B6A7B" }}>
                  <th className="text-left">Tag</th>
                  <th className="text-left">Attribute</th>
                  <th className="text-left">Value</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>(0008,0060)</td>
                  <td>Modality</td>
                  <td>DX</td>
                </tr>
                <tr>
                  <td>(0020,000D)</td>
                  <td>Study Instance UID</td>
                  <td>12.840...</td>
                </tr>
                <tr>
                  <td>(0008,0018)</td>
                  <td>SOP Instance UID</td>
                  <td>12.840...</td>
                </tr>
                <tr>
                  <td>(0008,0022)</td>
                  <td>Acquisition Date</td>
                  <td>2023.04.01</td>
                </tr>
                <tr>
                  <td>(0018,0060)</td>
                  <td>Kvp</td>
                  <td>120</td>
                </tr>
                <tr>
                  <td>(0018,5101)</td>
                  <td>View Position</td>
                  <td>AP</td>
                </tr>
              </tbody>
            </table>
            <button
              onClick={handleFindTag}
              className="text-blue-500 text-sm font-semibold mt-2 hover:underline"
            >
              View All Tags
            </button>
          </div>
        </div>
      </div>

      <div className="flex-col w-[90%]">
        <label className="flex mb-4 font-semibold text-[#26262C] text-xl">
          Clinical Notes
        </label>
        <div className="flex gap-4">
          <div className="flex flex-col bg-white rounded-xl space-y-4 ">
            <textarea
              value={clinicalNote}
              onChange={(e) => setClinicalNote(e.target.value)}
              placeholder="Radiology Clinical Reports"
              className="w-100 h-50 border rounded-md px-4 py-2 resize-none"
              style={{ borderColor: "#E4E4E8" }}
            />
            {standardizedResults.length == 0 ? (
              <button
                onClick={handleStandardize}
                className="flex justify-center items-center bg-blue-500 hover:bg-blue-400 text-white px-6 py-2 w-60 rounded-md font-semibold"
                disabled={isLoading}
              >
                {isLoading ? <Spinner /> : "Standardization"}
              </button>
            ) : (
              <button
                onClick={clearInputText}
                className="bg-blue-500 hover:bg-blue-400 text-white px-6 py-2 w-60 rounded-md font-semibold"
              >
                Clear
              </button>
            )}
          </div>
          {standardizedResults.length > 0 && (
            <div className="flex flex-col bg-white rounded-xl shadow px-6 py-4">
              <h3 className="text-lg font-semibold mb-4 text-[#26262C]">
                SNOMED CT Mapping Results
              </h3>
              <table className="table-auto w-full text-sm">
                <thead className="bg-gray-100 text-[#474653]">
                  <tr>
                    <th className="px-4 py-2 text-left">Hierarchy</th>
                    <th className="px-4 py-2 text-left">Input Description</th>
                    <th className="px-4 py-2 text-left">Concept Name</th>
                    <th className="px-4 py-2 text-left">Concept ID</th>
                  </tr>
                </thead>
                <tbody>
                  {standardizedResults.map((row, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-4 py-2">{row.Hierarchy}</td>
                      <td className="px-4 py-2">{row["Input Description"]}</td>
                      <td className="px-4 py-2">{row["Concept Name"]}</td>
                      <td className="px-4 py-2">{row["Concept ID"]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
