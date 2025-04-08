import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import About from "./pages/About";
import Features from "./pages/Features";
import Team from "./pages/Team";
import Playground from "./pages/Playground";
import Folder from "./pages/Folder";

export default function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/features" element={<Features />} />
        <Route path="/team" element={<Team />} />
        <Route path="/playground" element={<Playground />} />
        <Route path="/folder" element={<Folder />} />
      </Routes>
    </Router>
  );
}
