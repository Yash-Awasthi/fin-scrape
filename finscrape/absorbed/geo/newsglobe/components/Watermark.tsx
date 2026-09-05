"use client";

export default function Watermark() {
  return (
    <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-0 select-none">
      <h1 className="text-[12vw] font-black text-white/[0.03] tracking-widest uppercase">
        NEWSGLOBE
      </h1>
    </div>
  );
}
