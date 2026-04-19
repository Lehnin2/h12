import { useEffect, useState } from "react";

import { speakArabicText, stopVoicePlayback, supportsVoicePlayback } from "../lib/voiceAssistant";
import { UiIcon } from "./UiIcon";

interface VoiceAssistButtonProps {
  getText: () => string;
  idleLabel?: string;
  activeLabel?: string;
}

export function VoiceAssistButton({
  getText,
  idleLabel = "اسمع بالعربي",
  activeLabel = "وقف الصوت",
}: VoiceAssistButtonProps) {
  const [supported, setSupported] = useState(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    setSupported(supportsVoicePlayback());
  }, []);

  function handleClick() {
    if (!supported) return;

    if (playing) {
      stopVoicePlayback();
      setPlaying(false);
      return;
    }

    const started = speakArabicText(getText(), {
      onEnd: () => setPlaying(false),
      onError: () => setPlaying(false),
    });

    if (started) {
      setPlaying(true);
    }
  }

  return (
    <button
      type="button"
      className={`voice-button ${playing ? "is-active" : ""}`}
      onClick={handleClick}
      disabled={!supported}
      aria-label={playing ? activeLabel : idleLabel}
      title={supported ? idleLabel : "Voice unavailable on this device"}
    >
      <UiIcon name="voice" className="voice-button__icon" />
      <span>{playing ? activeLabel : idleLabel}</span>
    </button>
  );
}
