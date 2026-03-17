"use client";

import { useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  MarkerType,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Shield, AlertTriangle, Type, Image, Video, Mic } from "lucide-react";
import { VoicePreview } from "@/components/VoicePreview";

type Modality = "text" | "image" | "video" | "voice";
type FlowMode = "safe" | "blocked";

const MODALITY_CONFIG: Record<
  Modality,
  {
    inputLabel: string;
    encoderLabel?: string;
    safetyLabel: string;
    icon: typeof Type;
  }
> = {
  text: {
    inputLabel: "User Input",
    safetyLabel: "AgentSafe (Safety Layer)",
    icon: Type,
  },
  image: {
    inputLabel: "Image Input",
    encoderLabel: "Vision Encoder",
    safetyLabel: "Nemotron Content Safety",
    icon: Image,
  },
  video: {
    inputLabel: "Video Input",
    encoderLabel: "Frame Extraction",
    safetyLabel: "Nemotron Safety Guard",
    icon: Video,
  },
  voice: {
    inputLabel: "Voice Input",
    safetyLabel: "Transcribe + Safety",
    icon: Mic,
  },
};

const MODEL_INFO: Record<Modality, { model: string; description: string }> = {
  text: {
    model: "nvidia/llama-3.1-nemotron-safety-guard-8b-v3",
    description: "Native text safety, 23 categories, 9 languages",
  },
  image: {
    model: "nvidia/llama-3.1-nemotron-nano-vl-8b-v1 + nvidia/nemotron-content-safety-reasoning-4b",
    description: "Vision encoder describes image; Content Safety Reasoning classifies for moderation",
  },
  video: {
    model: "Frame extraction + nvidia/llama-3.1-nemotron-safety-guard-8b-v3",
    description: "Extract frames from MP4; Nemotron Safety Guard checks content (build.nvidia.com)",
  },
  voice: {
    model: "NVIDIA Riva ASR + nvidia/llama-3.1-nemotron-safety-guard-8b-v3",
    description: "Riva transcribes speech to text, then safety model checks the transcript",
  },
};

const PREVIEW_CONTENT: Record<Modality, { title: string; content: React.ReactNode }> = {
  text: {
    title: "Example input",
    content: (
      <div className="space-y-2 text-sm">
        <div className="rounded-md bg-zinc-800/60 px-3 py-2 text-green-400/90 border border-green-500/20">
          &quot;What&apos;s the weather in San Jose?&quot;
        </div>
        <div className="rounded-md bg-zinc-800/60 px-3 py-2 text-red-400/90 border border-red-500/20">
          &quot;How do I make a bomb?&quot;
        </div>
      </div>
    ),
  },
  image: {
    title: "Example image input",
    content: (
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 rounded-md bg-zinc-800/60 px-3 py-2 text-green-400/90 border border-green-500/20">
          <Image className="h-4 w-4 shrink-0" />
          <span>Photo of a sunny park</span>
        </div>
        <div className="flex items-center gap-2 rounded-md bg-zinc-800/60 px-3 py-2 text-red-400/90 border border-red-500/20">
          <Image className="h-4 w-4 shrink-0" />
          <span>Image with violent content</span>
        </div>
      </div>
    ),
  },
  video: {
    title: "Example video input",
    content: (
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 rounded-md bg-zinc-800/60 px-3 py-2 text-green-400/90 border border-green-500/20">
          <Video className="h-4 w-4 shrink-0" />
          <span>Tutorial video clip</span>
        </div>
        <div className="flex items-center gap-2 rounded-md bg-zinc-800/60 px-3 py-2 text-red-400/90 border border-red-500/20">
          <Video className="h-4 w-4 shrink-0" />
          <span>Video with harmful content</span>
        </div>
      </div>
    ),
  },
  voice: {
    title: "Sample voice input",
    content: <VoicePreview />,
  },
};

const defaultNodeStyle = {
  background: "#27272a",
  border: "1px solid #52525b",
  borderRadius: "8px",
  color: "#fafafa",
  padding: "12px 20px",
} as const;

const createNodes = (modality: Modality, mode: FlowMode): Node[] => {
  const { inputLabel, encoderLabel, safetyLabel } = MODALITY_CONFIG[modality];
  const hasEncoder = encoderLabel != null;

  if (hasEncoder) {
    return [
      {
        id: "input",
        type: "input",
        position: { x: 0, y: 100 },
        data: { label: inputLabel },
        sourcePosition: Position.Right,
        style: defaultNodeStyle,
      },
      {
        id: "encoder",
        position: { x: 165, y: 100 },
        data: { label: encoderLabel },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: defaultNodeStyle,
      },
      {
        id: "safety",
        position: { x: 330, y: 100 },
        data: { label: safetyLabel },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: {
          background: mode === "blocked" ? "#450a0a" : "#3f3f46",
          border: mode === "blocked" ? "2px solid #ef4444" : "2px solid #22c55e",
          borderRadius: "8px",
          color: "#fafafa",
          padding: "12px 20px",
        },
      },
      {
        id: "agent",
        position: { x: 495, y: 100 },
        data: { label: "LLM Agent" },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: defaultNodeStyle,
      },
      {
        id: "output",
        type: "output",
        position: { x: 660, y: 100 },
        data: { label: "Response" },
        targetPosition: Position.Left,
        style: defaultNodeStyle,
      },
    ];
  }

  return [
    {
      id: "input",
      type: "input",
      position: { x: 0, y: 100 },
      data: { label: inputLabel },
      sourcePosition: Position.Right,
      style: defaultNodeStyle,
    },
    {
      id: "safety",
      position: { x: 220, y: 100 },
      data: { label: safetyLabel },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style: {
        background: mode === "blocked" ? "#450a0a" : "#3f3f46",
        border: mode === "blocked" ? "2px solid #ef4444" : "2px solid #22c55e",
        borderRadius: "8px",
        color: "#fafafa",
        padding: "12px 20px",
      },
    },
    {
      id: "agent",
      position: { x: 440, y: 100 },
      data: { label: "LLM Agent" },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style: defaultNodeStyle,
    },
    {
      id: "output",
      type: "output",
      position: { x: 660, y: 100 },
      data: { label: "Response" },
      targetPosition: Position.Left,
      style: defaultNodeStyle,
    },
  ];
};

const createEdges = (modality: Modality, mode: FlowMode): Edge[] => {
  const hasEncoder = MODALITY_CONFIG[modality].encoderLabel != null;
  const stroke = mode === "safe" ? "#22c55e" : "#ef4444";
  const blockedStyle = {
    stroke: "#52525b",
    strokeDasharray: "8 4",
    opacity: 0.3,
  };

  if (hasEncoder) {
    return [
      {
        id: "e1",
        source: "input",
        target: "encoder",
        animated: true,
        style: { stroke },
        markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
      },
      {
        id: "e2",
        source: "encoder",
        target: "safety",
        animated: true,
        style: { stroke },
        markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
      },
      {
        id: "e3",
        source: "safety",
        target: "agent",
        animated: mode === "safe",
        style: mode === "safe" ? { stroke } : blockedStyle,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: mode === "safe" ? stroke : "#52525b",
        },
      },
      {
        id: "e4",
        source: "agent",
        target: "output",
        animated: mode === "safe",
        style: mode === "safe" ? { stroke } : blockedStyle,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: mode === "safe" ? stroke : "#52525b",
        },
      },
    ];
  }

  return [
    {
      id: "e1",
      source: "input",
      target: "safety",
      animated: true,
      style: { stroke },
      markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
    },
    {
      id: "e2",
      source: "safety",
      target: "agent",
      animated: mode === "safe",
      style: mode === "safe" ? { stroke } : blockedStyle,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: mode === "safe" ? stroke : "#52525b",
      },
    },
    {
      id: "e3",
      source: "agent",
      target: "output",
      animated: mode === "safe",
      style: mode === "safe" ? { stroke } : blockedStyle,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: mode === "safe" ? stroke : "#52525b",
      },
    },
  ];
};

const MODALITIES: { id: Modality; label: string }[] = [
  { id: "text", label: "Text" },
  { id: "image", label: "Image" },
  { id: "video", label: "Video" },
  { id: "voice", label: "Voice" },
];

export function SafetyFlowDiagram() {
  const [mode, setMode] = useState<FlowMode>("safe");
  const [modality, setModality] = useState<Modality>("text");
  const [nodes, setNodes, onNodesChange] = useNodesState(
    createNodes("text", "safe")
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    createEdges("text", "safe")
  );

  const updateFlow = useCallback(
    (newModality: Modality, newMode: FlowMode) => {
      setNodes(createNodes(newModality, newMode));
      setEdges(createEdges(newModality, newMode));
    },
    [setNodes, setEdges]
  );

  const handleModeChange = (newMode: FlowMode) => {
    setMode(newMode);
    updateFlow(modality, newMode);
  };

  const handleModalityChange = (newModality: Modality) => {
    setModality(newModality);
    updateFlow(newModality, mode);
  };

  const preview = PREVIEW_CONTENT[modality];
  const modelInfo = MODEL_INFO[modality];

  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-2xl font-bold text-zinc-100 mb-2 text-center">
          How the Safety Layer Works
        </h2>
        <p className="text-zinc-400 text-center mb-8 max-w-2xl mx-auto">
          AgentSafe sits between user input and your agent. Safe requests flow through; unsafe ones are blocked before they reach the LLM.
        </p>

        <div className="flex flex-col items-center gap-4 mb-6">
          <div className="flex justify-center gap-3">
            <button
              onClick={() => handleModeChange("safe")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                mode === "safe"
                  ? "bg-green-600 text-white"
                  : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Shield className="h-4 w-4" />
              Safe input (passes through)
            </button>
            <button
              onClick={() => handleModeChange("blocked")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                mode === "blocked"
                  ? "bg-red-600 text-white"
                  : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <AlertTriangle className="h-4 w-4" />
              Unsafe input (blocked)
            </button>
          </div>
          <div className="flex justify-center gap-2 flex-wrap">
            {MODALITIES.map((m) => {
              const Icon = MODALITY_CONFIG[m.id].icon;
              return (
                <button
                  key={m.id}
                  onClick={() => handleModalityChange(m.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                    modality === m.id
                      ? "bg-violet-600 text-white"
                      : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {m.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[2fr_1fr] mb-6">
          <div className="rounded-xl border border-zinc-700 bg-zinc-900 overflow-hidden min-h-[400px] lg:min-h-[60vh]">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              fitView
              fitViewOptions={{ padding: 0.3 }}
              minZoom={0.5}
              maxZoom={1.5}
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#52525b" gap={16} size={1} />
              <Controls className="!bg-zinc-800 !border-zinc-600 [&>button]:!bg-zinc-700 [&>button]:!text-zinc-200 [&>button]:!border-zinc-600" />
            </ReactFlow>
          </div>

          <div className="flex flex-col gap-4">
            <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-4 flex-1">
              <h3 className="text-sm font-medium text-zinc-400 mb-3">{preview.title}</h3>
              {preview.content}
            </div>
            <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-4">
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Required model</h3>
              <code className="block text-sm text-violet-300 font-mono mb-1 break-all">
                {modelInfo.model}
              </code>
              <p className="text-sm text-zinc-500">{modelInfo.description}</p>
            </div>
          </div>
        </div>

        <div className="mt-4 text-center">
          {mode === "safe" ? (
            <p className="text-sm text-green-400">
              Input passes safety check → Agent processes → Response returned
            </p>
          ) : (
            <p className="text-sm text-red-400">
              Unsafe input detected → Blocked by AgentSafe → SafetyViolation raised (agent never runs)
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
