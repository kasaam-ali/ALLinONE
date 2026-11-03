// Job: ALLinONE Frontend. Purpose: Shared Motion primitives (page fade, list stagger, KPI ticker) that respect reduced motion.
"use client";
import { animate, motion, useReducedMotion, type Variants } from "motion/react";
import { useEffect, useRef, type ReactNode } from "react";

const ease = [0.22, 1, 0.36, 1] as const;

export function Page({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <motion.div className="page" initial={reduce ? false : { opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.24, ease }}>
      {children}
    </motion.div>
  );
}

const list: Variants = { show: { transition: { staggerChildren: 0.035 } } };
const item: Variants = { hidden: { opacity: 0, y: 4 }, show: { opacity: 1, y: 0, transition: { duration: 0.2, ease } } };

export function StaggerBody({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();
  return <motion.tbody variants={list} initial={reduce ? false : "hidden"} animate="show">{children}</motion.tbody>;
}
export function Row({ children, className }: { children: ReactNode; className?: string }) {
  return <motion.tr variants={item} className={className}>{children}</motion.tr>;
}

export function Ticker({ value }: { value: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduce = useReducedMotion();
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (reduce) { el.textContent = String(value); return; }
    const c = animate(0, value, { duration: 0.8, ease, onUpdate: (v) => { el.textContent = String(Math.round(v)); } });
    return () => c.stop();
  }, [value, reduce]);
  return <span ref={ref} className="num">{reduce ? value : 0}</span>;
}
