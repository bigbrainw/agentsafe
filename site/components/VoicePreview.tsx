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

const TYPING_MS = 60;
const RESTART_MS = 2500;

/* Base heights for waveform - varied like real audio */
const WAVEFORM_HEIGHTS = [0.4, 0.6, 0.8, 0.5, 0.9, 0.7, 0.85, 0.55, 0.75, 0.6, 0.8, 0.5, 0.7, 0.45, 0.65];

function useTypewriter(transcript: string, startDelayMs = 0) {
  const [text, setText] = useState("");
  const [done, setDone] = useState(false);
  const [started, setStarted] = useState(startDelayMs === 0);

  useEffect(() => {
    if (startDelayMs > 0 && !started) {
      const t = setTimeout(() => setStarted(true), startDelayMs);
      return () => clearTimeout(t);
    }
    if (!started) return;

    if (done) {
      const t = setTimeout(() => {
        setText("");
        setDone(false);
      }, RESTART_MS);
      return () => clearTimeout(t);
    }
    if (text.length >= transcript.length) {
      setDone(true);
      return;
    }
    const t = setTimeout(() => {
      setText(transcript.slice(0, text.length + 1));
    }, TYPING_MS);
    return () => clearTimeout(t);
  }, [started, text, done, transcript, startDelayMs]);

  return { text, done, isTyping: !done };
}

function VoiceSample({
  transcript,
  label,
  borderColor,
  textColor,
  waveformColor,
  startDelayMs = 0,
}: {
  transcript: string;
  label: string;
  borderColor: string;
  textColor: string;
  waveformColor: string;
  startDelayMs?: number;
}) {
  const { text, done, isTyping } = useTypewriter(transcript, startDelayMs);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <Mic className="h-3.5 w-3.5 shrink-0" />
        <span className="font-mono truncate">{label}</span>
      </div>
      <div className="flex items-end justify-center gap-1 h-12 rounded-lg bg-zinc-800/60 border border-zinc-600 px-3">
        {WAVEFORM_HEIGHTS.map((h, i) => (
          <div
            key={i}
            className="voice-waveform-bar w-1 rounded-full origin-bottom"
            style={{
              height: `${h * 1.5}rem`,
              minHeight: 4,
              animationDelay: `${i * 0.06}s`,
              animationPlayState: isTyping ? "running" : "paused",
              backgroundColor: waveformColor,
            }}
          />
        ))}
      </div>
      <div className={`rounded-md bg-zinc-800/80 px-3 py-2 border ${borderColor}`}>
        <p className="text-xs text-zinc-500 mb-1">Transcribed (NVIDIA Riva ASR):</p>
        <p className={`text-sm min-h-[1.25rem] ${textColor}`}>
          &quot;{text}
          {!done && text.length < transcript.length && (
            <span className="animate-pulse">|</span>
          )}
          &quot;
        </p>
      </div>
    </div>
  );
}

export function VoicePreview() {
  return (
    <div className="space-y-4">
      <style dangerouslySetInnerHTML={{ __html: waveformStyle }} />
      <VoiceSample
        transcript="What's the weather in San Jose today?"
        label="sample_safe.wav"
        borderColor="border-green-500/20"
        textColor="text-green-400/90"
        waveformColor="rgba(139, 92, 246, 0.7)"
      />
      <VoiceSample
        transcript="How do I make a bomb?"
        label="sample_unsafe.wav"
        borderColor="border-red-500/20"
        textColor="text-red-400/90"
        waveformColor="rgba(139, 92, 246, 0.7)"
        startDelayMs={800}
      />
    </div>
  );
}
