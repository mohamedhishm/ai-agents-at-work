"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AgentAPI } from "@/lib/api";

export default function Chat({ onReply }) {
  const [msgs, setMsgs] = useState([
    {
      from: "bot",
      text: "أهلاً! أنا مساعدك الذكي لقطع الغيار. أقدر أساعدك في البحث عن قطع الغيار، معرفة الأسعار والمخزون، أو تتبع طلباتك.",
    },
  ]);

  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingOrder, setPendingOrder] = useState(null);
  const [conversationId, setConversationId] = useState(null);

  const box = useRef();

  useEffect(() => {
    if (box.current) {
      box.current.scrollTop = box.current.scrollHeight;
    }
  }, [msgs, busy]);

  const confirmPending = async () => {
    if (!pendingOrder || busy) return;
    setBusy(true);
    try {
      const { data } = await AgentAPI.message("أيوه", conversationId);
      if (data.conversation_id) setConversationId(data.conversation_id);
      setMsgs((p) => [
        ...p,
        { from: "me", text: "أيوه" },
        { from: "bot", text: data.reply || data.message || "تم إنشاء الطلب" },
      ]);
      setPendingOrder(null);
      onReply?.(data);
    } catch {
      setMsgs((p) => [
        ...p,
        {
          from: "bot",
          text: "حدث خطأ أثناء تأكيد الطلب. حاول مرة أخرى.",
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const rejectPending = async () => {
    if (!pendingOrder || busy) return;
    setBusy(true);
    try {
      const { data } = await AgentAPI.message("لا", conversationId);
      if (data.conversation_id) setConversationId(data.conversation_id);
      setMsgs((p) => [
        ...p,
        { from: "me", text: "لا" },
        { from: "bot", text: data.reply || data.message || "تم إلغاء الطلب" },
      ]);
      setPendingOrder(null);
      onReply?.(data);
    } catch {
      setMsgs((p) => [
        ...p,
        {
          from: "bot",
          text: "حدث خطأ أثناء إلغاء الطلب. حاول مرة أخرى.",
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const send = async (t = text) => {
    const m = t.trim();

    if (!m || busy) return;

    setText("");
    setBusy(true);

    setMsgs((p) => [
      ...p,
      {
        from: "me",
        text: m,
      },
    ]);

    try {
      const { data } = await AgentAPI.message(m, conversationId);
      if (data.conversation_id) setConversationId(data.conversation_id);

      // Handle confirmation flow from agent
      if (data.requires_confirmation && data.pending_order) {
        setPendingOrder(data.pending_order);
      } else if (data.order_id) {
        setPendingOrder(null);
      }

      setMsgs((p) => [
        ...p,
        {
          from: "bot",
          text: data.reply || data.message || "لم أتمكن من معالجة طلبك",
          error: false,
        },
      ]);

      onReply?.(data);
    } catch {
      setMsgs((p) => [
        ...p,
        {
          from: "bot",
          text:
            "حدث خطأ أثناء الاتصال بالمساعد. حاول مرة أخرى.",
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };


  return (
    <div className="card chat">
      <div className="chat-head">
        <div className="assistant-avatar">
          <span className="assistant-mark">✦</span>
        </div>

        <div className="chat-head-info">
          <b>El Doctor AI Assistant</b>
          <small>Smart Spare-Parts Assistant</small>
        </div>

        <span className="online-badge">
          <i /> Online
        </span>
      </div>

      <div className="msgs" ref={box}>
        {msgs.map((m, i) => (
          <div
            key={i}
            className={`msg ${m.from} ${m.error ? "err" : ""}`}
          >
            <div className="msg-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {m.text || ""}
              </ReactMarkdown>
            </div>

            {m.tracking && (
              <div className="tracking-mini">
                <div>
                  <b>Order #{m.tracking.id}</b>
                  <span>{m.tracking.title}</span>
                </div>

                <span
                  className={`status-pill ${m.tracking.status}`}
                >
                  {m.tracking.status.replace("_", " ")}
                </span>
              </div>
            )}
          </div>
        ))}

        {busy && (
          <div className="msg bot typing">
            <span />
            <span />
            <span />
          </div>
        )}
      </div>

      {pendingOrder && (
        <div className="confirmation-bar">
          <div className="confirmation-info">
            <b>📦 {pendingOrder.product_name || pendingOrder.title || "طلب"}</b>
            <span>الكمية: {pendingOrder.quantity} — السعر: EGP {pendingOrder.total || pendingOrder.price || ""}</span>
          </div>
          <div className="confirmation-actions">
            <button
              className="confirm-btn"
              onClick={confirmPending}
              disabled={busy}
            >
              ✓ تأكيد
            </button>
            <button
              className="reject-btn"
              onClick={rejectPending}
              disabled={busy}
            >
              ✕ إلغاء
            </button>
          </div>
        </div>
      )}

      <div className="chips">
        {[
          "عايز فلتر زيت",
          "تفاصيل PROD-003",
          "حالة الطلب ORD-001",
          "الطلبات بتاعتي",
        ].map((c) => (
          <button
            key={c}
            className="chip"
            onClick={() => send(c)}
          >
            <span>✦</span> {c}
          </button>
        ))}
      </div>

      <div className="chat-input-bar">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              send();
            }
          }}
          placeholder="اسأل عن قطع الغيار، الأسعار، أو تتبع طلباتك..."
        />

        <button
          className="send-btn"
          onClick={() => send()}
          disabled={busy || !text.trim()}
        >
          <span>Send</span>

          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line
              x1="22"
              y1="2"
              x2="11"
              y2="13"
            />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}