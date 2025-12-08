"use client";

import { useEffect, useRef, useState } from "react";
import { apiClient } from "@/lib/api/client";
import type { ChatMessageResponse, TaskResponse } from "@/lib/types/api";
import { getFriendlyErrorMessage } from "@/lib/utils/error";

type ChatMessage = {
  id: string;
  sender: "user" | "bot";
  text: string;
  taskTitle?: string;
};

interface TaskAssistantProps {
  onTaskCreated?: (task: TaskResponse) => void | Promise<void>;
}

export function TaskAssistant({ onTaskCreated }: TaskAssistantProps) {
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "bot",
      text: 'Tell me what to add and I\'ll create the task for you. Try "Add a task to call John."',
    },
  ]);
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages]);

  const appendBotMessage = (response: ChatMessageResponse) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: response.reply,
        taskTitle: response.created_task?.title,
      },
    ]);
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsSending(true);

    try {
      const response = await apiClient.chat.sendMessage({ message: trimmed });
      appendBotMessage(response);
      if (response.created_task && onTaskCreated) {
        await onTaskCreated(response.created_task);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-error-${Date.now()}`,
          sender: "bot",
          text: getFriendlyErrorMessage(
            error,
            "Sorry, I couldn't create that task. Try rephrasing it."
          ),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void sendMessage();
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 text-white shadow-xl">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.18),transparent_35%),radial-gradient(circle_at_80%_0%,rgba(16,185,129,0.15),transparent_30%)]" />
      <div className="relative space-y-4 p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-indigo-200/80">
              Task bot
            </p>
            <h3 className="text-xl font-ultra-bold tracking-tight text-white">Chat & Create</h3>
            <p className="text-sm text-slate-200/80">
              Type a sentence and I&apos;ll capture it as a new task.
            </p>
          </div>
        </div>

        <div ref={listRef} className="max-h-80 space-y-3 overflow-y-auto pr-1">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${msg.sender === "user"
                    ? "bg-indigo-500 text-white"
                    : "border border-white/10 bg-white/10 text-indigo-50"
                  }`}
              >
                <p className="text-sm leading-relaxed">{msg.text}</p>
                {msg.taskTitle && (
                  <span className="mt-2 inline-flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-100">
                    <span className="h-2 w-2 rounded-full bg-emerald-300" />
                    {msg.taskTitle}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Add a task to call John..."
            className="flex-1 rounded-xl border border-slate-700/80 bg-slate-800/80 px-3 py-3 text-sm text-white placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            className="rounded-xl bg-indigo-500 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-indigo-300/70"
          >
            {isSending ? "Sending..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
