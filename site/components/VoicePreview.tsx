"use client";

import { useEffect, useState } from "react";
import { Mic } from "lucide-react";

/* Inline styles ensure animation works regardless of Tailwind processing */
const waveformStyle = `
  @keyframes voice-waveform {
    0%, 100% { transform: scaleY(0.7); }
    50% { transform: scaleY(1); }
  }
  .voice-waveform-bar {
    animation: voice-waveform 1.8s ease-in-out infinite;
  }
`;

const TRANSCRIPT = "What's the weather in San Jose today?";
const TYPING_MS = 60;
const RESTART_MS = 2500;

/* Base heights for waveform - varied like real audio */
const WAVEFORM_HEIGHTS = [0.4, 0.6, 0.8, 0.5, 0.9, 0.7, 0.85, 0.55, 0.75, 0.6, 0.8, 0.5, 0.7, 0.45, 0.65];

export function VoicePreview() {
  const [text, setText] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (done) {
      const t = setTimeout(() => {
        setText("");
        setDone(false);
      }, RESTART_MS);
      return () => clearTimeout(t);
    }
    if (text.length >= TRANSCRIPT.length) {
      setDone(true);
      return;
    }
    const t = setTimeout(() => {
      setText(TRANSCRIPT.slice(0, text.length + 1));
    }, TYPING_MS);
    return () => clearTimeout(t);
  }, [text, done]);

  const isTyping = !done;

  return (
    <div className="space-y-3">
      <style dangerouslySetInnerHTML={{ __html: waveformStyle }} />
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <Mic className="h-3.5 w-3.5 shrink-0" />
        <span className="font-mono truncate">sample_voice.wav</span>
      </div>
      <div className="flex items-end justify-center gap-1 h-14 rounded-lg bg-zinc-800/60 border border-zinc-600 px-3">
        {WAVEFORM_HEIGHTS.map((h, i) => (
          <div
            key={i}
            className="voice-waveform-bar w-1.5 rounded-full bg-violet-500/70 origin-bottom"
            style={{
              height: `${h * 2}rem`,
              minHeight: 6,
              animationDelay: `${i * 0.06}s`,
              animationPlayState: isTyping ? "running" : "paused",
            }}
          />
        ))}
      </div>
      <div className="rounded-md bg-zinc-800/80 px-3 py-2 border border-zinc-600">
        <p className="text-xs text-zinc-500 mb-1">Transcribed (NVIDIA Riva ASR):</p>
        <p className="text-sm text-green-400/90 min-h-[1.5rem]">
          &quot;{text}
          {!done && text.length < TRANSCRIPT.length && (
            <span className="animate-pulse">|</span>
          )}
          &quot;
        </p>
      </div>
    </div>
  );
}
