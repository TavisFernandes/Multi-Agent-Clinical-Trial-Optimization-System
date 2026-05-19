import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { LandingPage } from "./components/LandingPage";
import { MedicalDashboard } from "./components/MedicalDashboard";

export default function App() {
  const [started, setStarted] = useState(false);

  return (
    <AnimatePresence mode="wait">
      {started ? (
        <motion.div
          key="dashboard"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -24 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="h-full w-full"
        >
          <MedicalDashboard />
        </motion.div>
      ) : (
        <motion.div
          key="landing"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="h-full w-full"
        >
          <LandingPage onStart={() => setStarted(true)} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
