import { motion } from "framer-motion";
import { SplineBackground } from "./SplineBackground";

interface LandingPageProps {
  onStart: () => void;
}

const fadeInUp = {
  initial: { opacity: 0, y: 40 },
  whileInView: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: "easeOut" },
  viewport: { once: true, margin: "0px 0px -100px 0px" },
};

const staggerContainer = {
  initial: { opacity: 0 },
  whileInView: { opacity: 1 },
  transition: { staggerChildren: 0.15 },
  viewport: { once: true },
};

export function LandingPage({ onStart }: LandingPageProps) {
  return (
    <div className="relative w-full overflow-x-hidden bg-navy text-white">
      {/* Hero Section */}
      <section className="relative min-h-screen w-full overflow-hidden">
        <SplineBackground />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(14,22,34,0.75),_rgba(4,8,15,0.95)_65%)]" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-black/10 to-black/95" />

        <div className="relative z-20 mx-auto flex min-h-screen max-w-[1360px] flex-col justify-center px-6 py-10 sm:px-10 lg:px-16">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center"
          >
            <div className="space-y-8">
              <div className="inline-flex items-center gap-3 rounded-full border border-teal-300/20 bg-teal-300/10 px-4 py-2 text-sm text-teal-100 backdrop-blur-sm w-fit">
                <span className="h-2.5 w-2.5 rounded-full bg-teal-300" />
                Clinical AI + Reasoning
              </div>
              <div className="space-y-6">
                <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                  Clinical Intelligence that thinks, reasons, and guides trial optimization.
                </h1>
                <p className="max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
                  From raw clinical text to structured reports, this immersive platform blends deep learning pipelines, multi-agent reasoning, and real-time interaction into a polished AI experience.
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-lg shadow-teal-500/10 backdrop-blur-xl">
                  <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Pipeline</p>
                  <p className="mt-3 text-lg font-semibold text-white">NER • LSTM • CV</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-lg shadow-cyan-500/10 backdrop-blur-xl">
                  <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Agents</p>
                  <p className="mt-3 text-lg font-semibold text-white">Architect + Critic + Retriever</p>
                </div>
              </div>
              <button
                type="button"
                onClick={onStart}
                className="w-fit inline-flex items-center justify-center rounded-full bg-teal-neon px-6 py-3 text-sm font-semibold text-navy shadow-[0_16px_40px_rgba(45,212,191,0.25)] transition hover:-translate-y-0.5 hover:bg-teal-400"
              >
                Get Started
              </button>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.75, ease: "easeOut" }}
              className="relative overflow-hidden rounded-[32px] border border-white/10 bg-slate-950/40 p-6 shadow-2xl shadow-black/40 backdrop-blur-xl"
            >
              <div className="pointer-events-none absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-black/40 to-transparent" />
              <div className="space-y-5">
                <div className="rounded-3xl border border-teal-400/10 bg-teal-400/5 p-5 text-slate-100">
                  <p className="text-xs uppercase tracking-[0.32em] text-teal-200/70">Storyline</p>
                  <p className="mt-3 text-base leading-7 text-slate-200">
                    Visualize a clinical assistant that parses trial protocols, identifies key entities, retrieves relevant studies, and refines findings with expert-level review.
                  </p>
                </div>
                <div className="grid gap-4">
                  <div className="rounded-3xl border border-white/10 bg-black/40 p-4 text-sm text-slate-300">
                    <p className="font-semibold text-white">Phase</p>
                    <p className="mt-2">Clinical text intake, entity extraction, model-driven interpretation.</p>
                  </div>
                  <div className="rounded-3xl border border-white/10 bg-black/40 p-4 text-sm text-slate-300">
                    <p className="font-semibold text-white">Outcome</p>
                    <p className="mt-2">Structured recommendations, trial matches, polished report.</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
            className="mt-12 flex items-center justify-center text-sm uppercase tracking-[0.3em] text-slate-500/80"
          >
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-teal-300">⇣</span>
            <span className="ml-3">Scroll to explore</span>
          </motion.div>
        </div>
      </section>

      {/* Content Sections */}
      <div className="relative z-10 w-full bg-navy">
        {/* Introduction */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">The Challenge</h2>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                  <p className="text-lg font-semibold text-teal-300 mb-3">Clinical trials are essential</p>
                  <p className="text-slate-300 leading-relaxed">Testing new medicines and treatments to ensure safety and effectiveness before public release.</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                  <p className="text-lg font-semibold text-teal-300 mb-3">Data overload</p>
                  <p className="text-slate-300 leading-relaxed">Massive volumes of unstructured, complex medical research generated daily.</p>
                </div>
              </div>
              <p className="text-base leading-8 text-slate-300">
                Manual analysis of clinical trial data is slow, inefficient, and prone to human error. The need for intelligent automation has never been greater.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Clinical Trial Fundamentals */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Clinical Trial Phases</h2>
              <p className="text-slate-300 leading-relaxed mb-6">Each clinical trial follows standardized phases to ensure safety and efficacy:</p>
              <motion.div variants={staggerContainer} className="grid gap-4 md:grid-cols-4">
                {[
                  { phase: "Phase 1", desc: "Safety Testing", detail: "Small group to test safety and dosage" },
                  { phase: "Phase 2", desc: "Effectiveness", detail: "Larger group to measure effectiveness" },
                  { phase: "Phase 3", desc: "Comparison", detail: "Compare to standard treatments" },
                  { phase: "Phase 4", desc: "Long-term", detail: "Monitor long-term effects post-launch" },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-teal-400/20 bg-teal-400/5 p-5 text-center"
                  >
                    <p className="text-sm font-bold text-teal-300">{item.phase}</p>
                    <p className="mt-2 text-sm font-semibold text-white">{item.desc}</p>
                    <p className="mt-2 text-xs text-slate-400">{item.detail}</p>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Problem Statement */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Why Manual Analysis Fails</h2>
              <div className="space-y-4">
                {[
                  { icon: "📊", title: "Large-scale Data", desc: "Thousands of research papers and trial records" },
                  { icon: "📄", title: "Unstructured Format", desc: "Text, reports, and medical jargon without standardization" },
                  { icon: "🧬", title: "Complex Interpretation", desc: "Requires expert medical knowledge to understand correctly" },
                  { icon: "⏳", title: "Time-Consuming", desc: "Manual review takes weeks or months per trial" },
                  { icon: "⚠️", title: "Error-Prone", desc: "Human fatigue leads to missed insights" },
                  { icon: "❌", title: "No Validation", desc: "Single output without cross-checking or refinement" },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-white/10 bg-white/5 p-5 flex gap-4 items-start"
                  >
                    <span className="text-2xl flex-shrink-0">{item.icon}</span>
                    <div>
                      <p className="font-semibold text-white">{item.title}</p>
                      <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* Solution Overview */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Our Solution</h2>
              <div className="rounded-3xl border border-teal-400/30 bg-teal-400/5 p-8">
                <p className="text-lg leading-8 text-slate-200 mb-6">
                  A multi-agent AI system that automatically analyzes clinical data, extracts key information, retrieves relevant trials, and validates outputs through iterative refinement.
                </p>
                <p className="text-sm text-teal-300 font-semibold">Key Insight:</p>
                <p className="text-slate-300 mt-2">Instead of one AI model producing a single answer, multiple specialized agents work together to analyze, improve, and validate results.</p>
              </div>
            </motion.div>
          </div>
        </section>

        {/* System Architecture */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">System Architecture</h2>
              <motion.div variants={staggerContainer} className="space-y-4">
                {[
                  { num: "1", title: "Input Layer", desc: "Clinical text or medical images uploaded by user" },
                  { num: "2", title: "Task Classifier", desc: "Determines input type (text, image, or hybrid)" },
                  { num: "3", title: "NLP Pipeline", desc: "Extracts entities (drugs, diseases, dosage) via NER" },
                  { num: "4", title: "LSTM Model", desc: "Understands clinical context and relationships" },
                  { num: "5", title: "Retriever Agent", desc: "Fetches relevant trials from database or API" },
                  { num: "6", title: "Architect Agent", desc: "Combines all data into structured report" },
                  { num: "7", title: "Critic Agent", desc: "Reviews and provides feedback for improvement" },
                  { num: "8", title: "Output Layer", desc: "Final validated clinical report and recommendations" },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-white/10 bg-white/5 p-5 flex gap-4"
                  >
                    <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-teal-neon/20 text-teal-300 font-semibold">
                      {item.num}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-white">{item.title}</p>
                      <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Key Components */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Core Technologies</h2>
              <motion.div variants={staggerContainer} className="grid gap-6 md:grid-cols-3">
                {[
                  {
                    icon: "🏷️",
                    title: "NER (Named Entity Recognition)",
                    techs: ["BC5CDR Model", "Extracts diseases, drugs, side effects", "Structured knowledge extraction"],
                  },
                  {
                    icon: "🧠",
                    title: "LSTM Neural Network",
                    techs: ["Understands context", "Learns temporal patterns", "Clinical interpretation"],
                  },
                  {
                    icon: "🔍",
                    title: "Multi-Agent System",
                    techs: ["Retriever Agent", "Architect Agent", "Critic Agent"],
                  },
                ].map((tech, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
                  >
                    <p className="text-4xl mb-3">{tech.icon}</p>
                    <p className="font-semibold text-white mb-4">{tech.title}</p>
                    <ul className="space-y-2 text-sm text-slate-300">
                      {tech.techs.map((t, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-teal-300">→</span> {t}
                        </li>
                      ))}
                    </ul>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Agentic AI Concept */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">What Makes It Unique: Agentic AI</h2>
              <div className="grid gap-6 md:grid-cols-2">
                <motion.div variants={fadeInUp} className="rounded-2xl border border-red-400/20 bg-red-400/5 p-8">
                  <p className="text-sm font-bold text-red-300 uppercase mb-3">Traditional AI</p>
                  <p className="text-3xl font-mono text-white mb-4">Input → Model → Output</p>
                  <p className="text-slate-300 text-sm">Single model processes input and produces one answer. No refinement or validation.</p>
                </motion.div>
                <motion.div variants={fadeInUp} className="rounded-2xl border border-teal-400/30 bg-teal-400/5 p-8">
                  <p className="text-sm font-bold text-teal-300 uppercase mb-3">Agentic AI (Our System)</p>
                  <p className="text-3xl font-mono text-white mb-4">Input → Agents → Validated Output</p>
                  <p className="text-slate-300 text-sm">Multiple agents collaborate, validate, and refine results iteratively for higher accuracy.</p>
                </motion.div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                <p className="font-semibold text-white mb-4">Agent Loop Mechanism:</p>
                <ol className="space-y-3 text-slate-300 text-sm">
                  <li>1️⃣ <strong>Retriever Agent</strong> finds relevant clinical trials</li>
                  <li>2️⃣ <strong>Architect Agent</strong> generates structured report combining all data</li>
                  <li>3️⃣ <strong>Critic Agent</strong> reviews and identifies gaps</li>
                  <li>4️⃣ System loops 2–3 times until quality threshold is met</li>
                  <li>5️⃣ Final polished report is delivered to user</li>
                </ol>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Working Example */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Real-World Example</h2>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-8">
                <p className="text-teal-300 font-semibold mb-4">📝 Input Query:</p>
                <p className="text-white font-mono text-lg bg-black/40 p-4 rounded-lg mb-8">
                  "Find Phase II diabetes drugs with cardiovascular side effects and patient count &gt; 100"
                </p>

                <p className="text-teal-300 font-semibold mb-4">🔧 System Processing:</p>
                <div className="space-y-3 mb-8 text-slate-300 text-sm">
                  <p>• NER extracts: <strong>diabetes, Phase II, cardiovascular, 100+ patients</strong></p>
                  <p>• LSTM analyzes clinical relationships and context</p>
                  <p>• Retriever finds matching trials from database</p>
                  <p>• Architect creates structured report with all details</p>
                  <p>• Critic validates completeness and accuracy</p>
                </div>

                <p className="text-teal-300 font-semibold mb-4">📊 System Output:</p>
                <div className="bg-black/40 p-4 rounded-lg text-sm text-slate-300 font-mono">
                  <p>Trial: XYZ-4567</p>
                  <p>Phase: II | Drug: Metformin+ | Patients: 245</p>
                  <p>Condition: Type 2 Diabetes</p>
                  <p>Side Effect: Increased heart rate (7.2%)</p>
                  <p>Status: Enrolling | Cost: $2.5M</p>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Advantages */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Key Advantages</h2>
              <motion.div variants={staggerContainer} className="grid gap-4 md:grid-cols-2">
                {[
                  { emoji: "⏳", title: "Saves Time", desc: "Analyzes in seconds vs weeks of manual work" },
                  { emoji: "💪", title: "Reduces Manual Effort", desc: "Minimal human input required after setup" },
                  { emoji: "✅", title: "Higher Accuracy", desc: "Multi-agent validation reduces errors" },
                  { emoji: "📄", title: "Handles Complexity", desc: "Processes unstructured medical text seamlessly" },
                  { emoji: "📊", title: "Structured Output", desc: "Clean JSON/reports instead of raw text" },
                  { emoji: "🔄", title: "Iterative Refinement", desc: "Self-improving through agent feedback loops" },
                ].map((adv, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-white/10 bg-white/5 p-5"
                  >
                    <p className="text-2xl mb-2">{adv.emoji}</p>
                    <p className="font-semibold text-white">{adv.title}</p>
                    <p className="text-sm text-slate-400 mt-2">{adv.desc}</p>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Applications */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Real-World Applications</h2>
              <motion.div variants={staggerContainer} className="grid gap-6 md:grid-cols-2">
                {[
                  { icon: "🏥", title: "Healthcare Research", desc: "Accelerate medical discovery and trial analysis" },
                  { icon: "💊", title: "Pharmaceutical Companies", desc: "Speed up drug development and approval" },
                  { icon: "🔬", title: "Drug Discovery", desc: "Identify promising compounds faster" },
                  { icon: "🏛️", title: "Regulatory Bodies", desc: "Review trial data for approval decisions" },
                  { icon: "👨‍⚕️", title: "Doctors & Clinicians", desc: "Decision support for treatment selection" },
                  { icon: "🎓", title: "Medical Education", desc: "Train next generation on trial analysis" },
                ].map((app, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-white/10 bg-white/5 p-6"
                  >
                    <p className="text-3xl mb-3">{app.icon}</p>
                    <p className="font-semibold text-white">{app.title}</p>
                    <p className="text-sm text-slate-400 mt-2">{app.desc}</p>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Limitations */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Limitations & Challenges</h2>
              <div className="rounded-2xl border border-yellow-400/20 bg-yellow-400/5 p-8">
                <p className="text-sm text-yellow-300 font-semibold mb-4">Honest Challenges We Face:</p>
                <motion.div variants={staggerContainer} className="space-y-4">
                  {[
                    "Not 100% accurate — depends on input data quality",
                    "Requires computational resources for deep learning models",
                    "Medical knowledge base must be continuously updated",
                    "Language barriers may affect non-English clinical data",
                    "Regulatory compliance needs careful attention",
                  ].map((limit, idx) => (
                    <motion.p key={idx} variants={fadeInUp} className="text-slate-300 flex gap-3">
                      <span className="text-yellow-300">⚠️</span> {limit}
                    </motion.p>
                  ))}
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Future Roadmap */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Future Roadmap</h2>
              <motion.div variants={staggerContainer} className="grid gap-6 md:grid-cols-2">
                {[
                  { title: "Real-time Database Integration", detail: "Connect to live ClinicalTrials.gov API continuously" },
                  { title: "Advanced LLM Models", detail: "Upgrade to ChatGPT/Claude for better reasoning" },
                  { title: "Personalized Medicine", detail: "Recommend treatments based on individual patient profiles" },
                  { title: "Auto Web Deployment", detail: "One-click cloud deployment (AWS/GCP)" },
                  { title: "Multi-language Support", detail: "Support clinical trials in 20+ languages" },
                  { title: "Mobile Application", detail: "iOS/Android app for on-the-go trial lookup" },
                ].map((roadmap, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-teal-400/20 bg-teal-400/5 p-6"
                  >
                    <p className="font-semibold text-teal-300 flex gap-2">
                      <span>🚀</span> {roadmap.title}
                    </p>
                    <p className="text-sm text-slate-300 mt-2">{roadmap.detail}</p>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8">
              <h2 className="text-4xl font-semibold text-white">Technology Stack</h2>
              <div className="grid gap-6 md:grid-cols-3">
                {[
                  {
                    category: "Backend",
                    techs: ["Python", "FastAPI", "WebSockets", "TensorFlow/PyTorch"],
                  },
                  {
                    category: "ML Models",
                    techs: ["NER (BC5CDR)", "LSTM Networks", "CNN/ResNet", "Transformers"],
                  },
                  {
                    category: "Frontend",
                    techs: ["React + TypeScript", "Three.js (3D)", "Framer Motion", "Tailwind CSS"],
                  },
                  {
                    category: "Data",
                    techs: ["PostgreSQL", "Vector DB", "Clinical Datasets", "ClinicalTrials API"],
                  },
                  {
                    category: "Deployment",
                    techs: ["Docker", "Kubernetes", "AWS/GCP", "CI/CD Pipelines"],
                  },
                  {
                    category: "Tools",
                    techs: ["Git", "Jupyter", "VS Code", "Postman"],
                  },
                ].map((stack, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeInUp}
                    className="rounded-2xl border border-white/10 bg-white/5 p-6"
                  >
                    <p className="font-semibold text-white mb-4">{stack.category}</p>
                    <ul className="space-y-2 text-sm text-slate-300">
                      {stack.techs.map((tech, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-teal-300">✓</span> {tech}
                        </li>
                      ))}
                    </ul>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* Conclusion & CTA */}
        <section className="border-t border-white/10 px-6 py-20 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl">
            <motion.div {...fadeInUp} className="space-y-8 text-center">
              <h2 className="text-4xl font-semibold text-white">Ready to Transform Clinical Trials?</h2>
              <p className="text-lg leading-8 text-slate-300 max-w-2xl mx-auto">
                This is not just an AI model—it's a complete ecosystem for intelligent healthcare innovation. Multi-agent reasoning, real-time pipelines, and scalable deployment combined into one polished experience.
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onStart}
                className="inline-flex items-center justify-center rounded-full bg-teal-neon px-8 py-4 text-base font-semibold text-navy shadow-[0_20px_50px_rgba(45,212,191,0.3)] transition hover:-translate-y-1"
              >
                Explore the Dashboard Now
              </motion.button>
            </motion.div>
          </div>
        </section>

        {/* Footer */}
        <section className="border-t border-white/10 px-6 py-12 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-5xl text-center">
            <motion.div {...fadeInUp} className="space-y-4">
              <p className="text-sm text-slate-500">
                Multi-Agent Clinical Trial Optimization System
              </p>
              <p className="text-xs text-slate-600">
                AI-powered healthcare innovation | Data Science Project
              </p>
            </motion.div>
          </div>
        </section>
      </div>
    </div>
  );
}
