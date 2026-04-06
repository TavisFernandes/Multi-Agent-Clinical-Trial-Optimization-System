import { motion } from "framer-motion";

/** DOM-layer scan accent (pairs with 3D beam during Processing). */
export function ScanBeamOverlay({ active }: { active: boolean }) {
  return (
    <motion.div
      className="pointer-events-none fixed inset-0 z-[12] overflow-hidden border border-white/5"
      initial={false}
      animate={{ opacity: active ? 1 : 0 }}
      transition={{ duration: 0.35 }}
    >
      <motion.div
        className="absolute inset-x-0 top-0 h-[28%] bg-gradient-to-b from-teal-neon/30 to-transparent blur-lg"
        initial={false}
        animate={
          active
            ? { top: ["-10%", "110%"] }
            : { top: "-10%" }
        }
        transition={{ duration: 2.2, ease: "easeInOut" }}
      />
    </motion.div>
  );
}
