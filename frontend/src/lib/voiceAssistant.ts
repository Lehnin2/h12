function pickArabicVoice(voices: SpeechSynthesisVoice[]) {
  return (
    voices.find((voice) => voice.lang.toLowerCase() === "ar-tn") ??
    voices.find((voice) => voice.lang.toLowerCase() === "ar-sa") ??
    voices.find((voice) => voice.lang.toLowerCase().startsWith("ar")) ??
    null
  );
}

export function supportsVoicePlayback() {
  return typeof window !== "undefined" && "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

export function stopVoicePlayback() {
  if (supportsVoicePlayback()) {
    window.speechSynthesis.cancel();
  }
}

export function speakArabicText(
  text: string,
  callbacks?: {
    onEnd?: () => void;
    onError?: () => void;
  },
) {
  if (!supportsVoicePlayback()) {
    callbacks?.onError?.();
    return false;
  }

  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  const selectedVoice = pickArabicVoice(voices);

  utterance.lang = selectedVoice?.lang ?? "ar-TN";
  if (selectedVoice) utterance.voice = selectedVoice;
  utterance.rate = 0.95;
  utterance.pitch = 1;
  utterance.volume = 1;

  utterance.onend = () => callbacks?.onEnd?.();
  utterance.onerror = () => callbacks?.onError?.();

  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
  return true;
}
