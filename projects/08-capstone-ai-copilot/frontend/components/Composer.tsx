/**
 * ============================================================================
 *  COMPOSER — where a turn gets built: text, an optional image, or your voice
 * ============================================================================
 * Three ways to put words in the box: type them, attach an image (sent
 * alongside your text so the agent's describe_image tool has something to
 * work with), or record your voice — which gets transcribed (Project 7's
 * /transcribe endpoint, reusing the same MediaRecorder pattern) straight
 * into the text box rather than sent automatically, so you can review or
 * edit what it heard before it becomes a real message to the agent.
 * ============================================================================
 */

"use client";

import { useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Composer({
  onSend,
  disabled,
}: {
  onSend: (text: string, image: File | null) => void;
  disabled: boolean;
}) {
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  function handleImagePick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setImage(file);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(file ? URL.createObjectURL(file) : null);
  }

  function clearImage() {
    setImage(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        transcribe(new Blob(chunksRef.current, { type: recorder.mimeType }));
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch {
      // Microphone permission denied or unavailable — nothing to recover
      // into here, the record button just stays available to try again.
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  async function transcribe(audioBlob: Blob) {
    setTranscribing(true);
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      formData.append("provider", "local");
      const res = await fetch(`${API_URL}/transcribe`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.text) setText((prev) => (prev ? `${prev} ${data.text}` : data.text));
    } catch {
      // Transcription failure isn't fatal — the box just stays empty and
      // you can type instead.
    } finally {
      setTranscribing(false);
    }
  }

  function handleSend() {
    if (!text.trim() || disabled) return;
    onSend(text.trim(), image);
    setText("");
    clearImage();
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-black/10 dark:border-white/15 p-3">
      {imagePreview && (
        <div className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element -- a locally picked file has no URL to optimize */}
          <img src={imagePreview} alt="Attached" className="h-16 rounded border border-black/10 dark:border-white/15" />
          <button onClick={clearImage} className="text-xs opacity-60 hover:opacity-100">
            Remove
          </button>
        </div>
      )}

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        rows={2}
        placeholder={transcribing ? "Transcribing…" : "Ask something, attach an image, or record your voice…"}
        className="w-full resize-none border-0 bg-transparent text-sm outline-none"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label className="cursor-pointer text-xs opacity-60 hover:opacity-100">
            📎 Attach image
            <input type="file" accept="image/*" onChange={handleImagePick} className="hidden" />
          </label>
          <button
            onClick={recording ? stopRecording : startRecording}
            className={`text-xs ${recording ? "text-red-600 dark:text-red-400" : "opacity-60 hover:opacity-100"}`}
          >
            {recording ? "■ Stop recording" : "● Record voice"}
          </button>
        </div>
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="rounded-lg bg-black px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
        >
          {disabled ? "Thinking…" : "Send"}
        </button>
      </div>
    </div>
  );
}
