/**
 * Spline robot as full-bleed background. Phase 1 integration.
 * Now interactable with mouse - users can click and drag the robot.
 */
export function SplineBackground() {
  return (
    <iframe
      className="fixed inset-0 h-full w-full border-0 opacity-[0.58] cursor-grab active:cursor-grabbing"
      title="Spline 3D Greeting Robot"
      src="https://my.spline.design/genkubgreetingrobot-TLLJghI7cQ9RUE9p4Zi55w21/"
      loading="lazy"
      allow="fullscreen"
      style={{ pointerEvents: "auto" }}
    />
  );
}
