import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";

import { useAppContext } from "../app/AppContext";
import { sendChatMessage } from "../lib/api";
import { uiCopy } from "../lib/uiCopy";
import type { ChatMessageResponse, ChatToolSnapshot, ChatTurn } from "../types";
import { UiIcon } from "./UiIcon";
import { VoiceAssistButton } from "./VoiceAssistButton";

type PageKey = "heatmap" | "route" | "lunar" | "safety" | "profile" | "admin";

interface AssistantMessage extends ChatTurn {
  voiceTextAr?: string | null;
  toolsUsed?: ChatToolSnapshot[];
  suggestedPrompts?: string[];
  usedLlm?: boolean;
}

function pageKeyFromPath(pathname: string): PageKey {
  if (pathname.startsWith("/route")) return "route";
  if (pathname.startsWith("/lunar")) return "lunar";
  if (pathname.startsWith("/safety")) return "safety";
  if (pathname.startsWith("/profile")) return "profile";
  if (pathname.startsWith("/admin")) return "admin";
  return "heatmap";
}

function defaultPrompts(page: PageKey): string[] {
  switch (page) {
    case "route":
      return ["Pourquoi cette route ?", "Où est le risque principal ?", "Le fuel est-il suffisant ?"];
    case "lunar":
      return ["Le meilleur moment aujourd'hui ?", "La lune aide quelle espèce ?", "Explique la fenêtre de pêche"];
    case "safety":
      return ["Puis-je sortir maintenant ?", "Que faire avant départ ?", "Explique la safety simplement"];
    case "profile":
      return ["Explique mes données mission", "Que disent les pêcheurs ?", "Pourquoi la météo compte ici ?"];
    case "admin":
      return ["Quelle zone est sous pression ?", "Quels incidents safety récents ?", "Les sources sont-elles fraîches ?"];
    default:
      return ["Pourquoi cette zone ?", "Cette zone est-elle légale ?", "Puis-je partir maintenant ?"];
  }
}

export function ChatAssistant() {
  const { pathname } = useLocation();
  const { token, uiLanguage, mission } = useAppContext();
  const copy = uiCopy[uiLanguage].chat;
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [currentTools, setCurrentTools] = useState<ChatToolSnapshot[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const threadRef = useRef<HTMLDivElement | null>(null);
  const page = useMemo(() => pageKeyFromPath(pathname), [pathname]);

  useEffect(() => {
    setSuggestions(defaultPrompts(page));
    setError(null);
  }, [page]);

  useEffect(() => {
    if (!threadRef.current) return;
    threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [messages, open, busy]);

  async function submitMessage(rawMessage?: string) {
    const message = (rawMessage ?? draft).trim();
    if (!message || !token || busy) return;

    const nextUserMessage: AssistantMessage = { role: "user", content: message };
    const nextHistory: ChatTurn[] = [...messages, nextUserMessage].map(({ role, content }) => ({ role, content }));

    setBusy(true);
    setError(null);
    setDraft("");
    setMessages((current) => [...current, nextUserMessage]);

    try {
      const response: ChatMessageResponse = await sendChatMessage(token, {
        message,
        page,
        history: nextHistory.slice(-8),
      });

      const assistantMessage: AssistantMessage = {
        role: "assistant",
        content: response.answer,
        voiceTextAr: response.voice_text_ar,
        toolsUsed: response.tools_used,
        suggestedPrompts: response.suggested_prompts,
        usedLlm: response.used_llm,
      };
      setMessages((current) => [...current, assistantMessage]);
      setCurrentTools(response.tools_used);
      setSuggestions(response.suggested_prompts.length ? response.suggested_prompts : defaultPrompts(page));
    } catch {
      const fallback = mission?.recommendation?.advisory
        ? `Je n'ai pas pu joindre l'assistant live. Conseil mission actuel: ${mission.recommendation.advisory}`
        : "Je n'ai pas pu joindre l'assistant live pour le moment. Réessaie dans quelques secondes.";
      setMessages((current) => [...current, { role: "assistant", content: fallback }]);
      setError("Assistant temporairement indisponible.");
    } finally {
      setBusy(false);
    }
  }

  function handleVoiceInput() {
    const Recognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!Recognition) {
      setError("Désolé, votre navigateur ne supporte pas la reconnaissance vocale.");
      return;
    }

    const recognition = new Recognition();
    recognition.lang = uiLanguage === "tn" ? "ar-TN" : uiLanguage === "fr" ? "fr-FR" : "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setDraft(transcript);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
      setError(`Erreur micro: ${event.error}`);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  }

  return (
    <>
      <button
        type="button"
        className={`chat-launcher ${open ? "is-open" : ""}`}
        onClick={() => setOpen((value) => !value)}
        aria-label={open ? copy.close : copy.launcher}
      >
        <span className="chat-launcher__icon-wrap">
          <UiIcon name="chat" className="chat-launcher__icon" />
        </span>
        <span className="chat-launcher__label">{copy.launcher}</span>
      </button>

      <aside className={`chat-sheet ${open ? "is-open" : ""}`} aria-hidden={!open} dir={uiLanguage === 'tn' ? 'rtl' : 'ltr'}>
        <header className="chat-sheet__header">
          <div className="chat-sheet__title-area">
            <p className="chat-sheet__eyebrow">{copy.launcher}</p>
            <h3>{copy.title}</h3>
            <p>{copy.subtitle}</p>
          </div>
          <button type="button" className="chat-sheet__close" onClick={() => setOpen(false)} aria-label={copy.close}>
            <UiIcon name="close" />
          </button>
        </header>

        <div className="chat-thread" ref={threadRef}>
          {messages.length === 0 ? (
            <div className="chat-empty-state">
              <strong>{copy.suggestions}</strong>
              <p>
                {page === "heatmap"
                  ? (uiLanguage === 'tn' ? 'إسأل علاش البلاصة هذي، ولا كان تنجم تخرج، ولا شنوة قالو البحارة.' : (uiLanguage === 'fr' ? "Demande pourquoi la zone est choisie, si tu peux partir, ou ce que disent les pêcheurs." : "Ask why the zone was chosen, if you can depart, or what other fishermen are saying."))
                  : (uiLanguage === 'tn' ? 'إسأل سؤال قصير. العون يجاوبك بالمعلومات اللي في الصفحة هذي.' : (uiLanguage === 'fr' ? "Pose une question courte. L'assistant répond avec les données backend de la page actuelle." : "Ask a short question. The assistant answers with the current page's backend data."))}
              </p>
            </div>
          ) : null}

          {messages.map((message, index) => (
            <article
              key={`${message.role}-${index}-${message.content.slice(0, 24)}`}
              className={`chat-bubble chat-bubble--${message.role}`}
            >
              <div className="chat-bubble__meta">
                <span>{message.role === "user" ? (uiLanguage === 'tn' ? 'أنت' : (uiLanguage === 'fr' ? 'Vous' : 'You')) : copy.title}</span>
                {message.role === "assistant" && message.usedLlm !== undefined ? (
                  <small>{message.usedLlm ? "Groq AI" : "Local Data"}</small>
                ) : null}
              </div>
              <div className="chat-bubble__content">
                <p>{message.content}</p>

                {message.role === "assistant" && message.voiceTextAr ? (
                  <VoiceAssistButton
                    getText={() => message.voiceTextAr ?? ""}
                    idleLabel={copy.listen}
                    activeLabel={copy.stop}
                  />
                ) : null}

                {message.role === "assistant" && message.toolsUsed?.length ? (
                  <div className="chat-tools">
                    {message.toolsUsed.map((tool) => (
                      <span key={tool.tool_name} className="chat-tools__chip" title={tool.summary}>
                        {tool.tool_name.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            </article>
          ))}

          {busy ? <div className="chat-loading">{copy.loading}</div> : null}
          {error ? <div className="chat-error">{error}</div> : null}
        </div>

        <div className="chat-footer">
          <div className="chat-prompt-row">
            {suggestions.map((suggestion) => (
              <button
                key={`${page}-${suggestion}`}
                type="button"
                className="chat-prompt"
                onClick={() => void submitMessage(suggestion)}
                disabled={busy}
              >
                {suggestion}
              </button>
            ))}
          </div>

          <form
            className="chat-composer"
            onSubmit={(event) => {
              event.preventDefault();
              void submitMessage();
            }}
          >
            <button
              type="button"
              className={`chat-composer__micro ${isListening ? "is-active" : ""}`}
              onClick={handleVoiceInput}
              disabled={busy}
              title="Voice Input"
            >
              <UiIcon name="micro" />
            </button>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={copy.placeholder}
              rows={1}
              maxLength={500}
            />
            <button type="submit" className="chat-composer__submit" disabled={busy || !draft.trim()}>
              <UiIcon name="chat" />
            </button>
          </form>
        </div>
      </aside>
    </>
  );
}
