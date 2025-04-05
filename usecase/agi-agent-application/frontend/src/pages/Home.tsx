import { Link } from "react-router-dom";
import computerImage from "../assets/computer.png";
import { CTAButton } from "../components/CTAButton";

export default function Home() {
  return (
    <div className="flex justify-between p-16 flex-col-reverse lg:flex-row">
      <div className="max-w-lg">
        <div className="text-[3rem] text-neutral-1 mb-1 font-bold">RADRAG</div>
        <div className="text-[2rem] text-neutral-2 mb-3 font-bold">
          Standardization Tool of Radiology Free-text
        </div>
        <div className="text-body1 text-[#6B6A7B] mb-8">
          Make smart clinical decisions and seamless claims with RADRAG – your
          LLM-based standardization tool for radiology free-text.
        </div>
        <Link to="/playground" className="flex">
          <CTAButton name={"Real-time Standardization"} />
        </Link>
      </div>
      <img
        src={computerImage}
        alt="illustration"
        className="max-w-xl mb-8 lg:mb-0"
      />
    </div>
  );
}
