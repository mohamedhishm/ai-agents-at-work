"use client";

import { useEffect, useRef, useState } from "react";
import { AgentAPI, TaskAPI } from "@/lib/api";

const isStockRequest = (value) => {
  const t = value.toLowerCase();

  const enMatch =
    /\b(stock|available|availability|in stock|price|prices|cost|how much)\b/.test(
      t
    ) &&
    !/\b(track|tracking|where is|status|delivery|delivered|shipment|order)\b/.test(
      t
    );

  const arMatch =
    /(مخزن|المخزن|المتاح|متاحة|اسعار|أسعار|سعر|كمية|بكام|عندكم)/.test(t) &&
    !/(تتبع|فين|مكان|شحنة)/.test(t);

  return enMatch || arMatch;
};

const isTrackingRequest = (value) => {
  const t = value.toLowerCase();

  const enMatch =
    /(where is|track|tracking|status).*(order|package|delivery)/.test(t) ||
    /where.*(order|package|delivery)/.test(t);

  const arMatch =
    /(تتبع|فين|مكان|الطلب|الأوردر|الاوردر|الشحنة)/.test(t);

  return enMatch || arMatch;
};

const isPartSearchRequest = (value) => {
  const t = value.toLowerCase();

  const enMatch =
    /\b(find|search|look for|looking for|need|want)\b/.test(t) &&
    /\b(part|parts|brake|pads|filter|spark plugs|disc|spare)\b/.test(t);

  const arMatch =
    /(عايز|عايزة|محتاج|محتاجة|بحث|دور|فرامل|تيل|فلتر|بوجيهات|دسك|قطع|قطعة|حاجة|هيونداي|خيونداي|كيا|نيسان|شفروليه)/.test(
      t
    );

  return enMatch || arMatch;
};

const BRANDS = {
  hyundai: [
    "هيونداي",
    "خيونداي",
    "هيونداى",
    "hyundai",
    "إلنترا",
    "النترا",
    "elantra",
    "توسان",
    "tucson",
  ],
  kia: [
    "كيا",
    "kia",
    "سيراتو",
    "cerato",
    "سبورتاج",
    "sportage",
  ],
  chevrolet: [
    "شفروليه",
    "شيفروليه",
    "chevrolet",
    "أفيو",
    "افيو",
    "aveo",
  ],
  nissan: ["نيسان", "nissan", "صني", "sunny"],
};

const STOCK = [
  {
    brand: "hyundai",
    title:
      "تيل فرامل أمامي - هيونداي إلنترا (Hyundai Elantra Front Brake Pads)",
    keywords: [
      "هيونداي",
      "خيونداي",
      "إلنترا",
      "النترا",
      "hyundai",
      "elantra",
      "تيل",
      "فرامل",
      "brake",
    ],
    stock: 12,
    price: 189,
  },
  {
    brand: "hyundai",
    title: "فلتر زيت - هيونداي توسان (Hyundai Tucson Oil Filter)",
    keywords: [
      "هيونداي",
      "خيونداي",
      "توسان",
      "hyundai",
      "tucson",
      "فلتر",
      "زيت",
      "filter",
    ],
    stock: 9,
    price: 210,
  },
  {
    brand: "kia",
    title: "فلتر زيت - كيا سيراتو (Kia Cerato Oil Filter)",
    keywords: [
      "كيا",
      "kia",
      "سيراتو",
      "cerato",
      "فلتر",
      "زيت",
      "filter",
    ],
    stock: 8,
    price: 420,
  },
  {
    brand: "chevrolet",
    title: "فلتر هواء - شفروليه أفيو (Chevrolet Aveo Air Filter)",
    keywords: [
      "شفروليه",
      "شيفروليه",
      "chevrolet",
      "أفيو",
      "افيو",
      "aveo",
      "فلتر",
      "هواء",
      "filter",
    ],
    stock: 5,
    price: 59,
  },
  {
    brand: "nissan",
    title: "طقم بوجيهات محرك - نيسان صني (Nissan Sunny Spark Plugs)",
    keywords: [
      "نيسان",
      "nissan",
      "صني",
      "sunny",
      "بوجيهات",
      "spark",
    ],
    stock: 16,
    price: 95,
  },
  {
    brand: "kia",
    title: "دسك فرامل خلفي - كيا سبورتاج (Kia Sportage Brake Disc)",
    keywords: [
      "كيا",
      "kia",
      "سبورتاج",
      "sportage",
      "دسك",
      "فرامل",
      "disc",
      "brake",
    ],
    stock: 3,
    price: 140,
  },
];

const STOPWORDS = new Set([
  "عايز",
  "عايزة",
  "عايزين",
  "محتاج",
  "محتاجة",
  "حاجة",
  "حاجه",
  "لـ",
  "ل",
  "إيه",
  "اي",
  "هات",
  "ممكن",
  "لو",
  "سمحت",
  "want",
  "need",
  "find",
  "search",
  "looking",
  "something",
  "for",
  "part",
  "parts",
]);

const statusTextEn = {
  processing: "being prepared",
  shipped: "on the way",
  delivered: "delivered",
  pending_approval: "waiting for approval",
  rejected: "rejected",
  cancelled: "cancelled",
};

const detectBrand = (text) => {
  const lo = text.toLowerCase();

  for (const [brand, aliases] of Object.entries(BRANDS)) {
    if (aliases.some((alias) => lo.includes(alias))) {
      return brand;
    }
  }

  return null;
};

const getSelectionIndex = (text) => {
  const lo = text.toLowerCase().trim();

  const normalized = lo.replace(/[٠-٩]/g, (d) =>
    "٠١٢٣٤٥٦٧٨٩".indexOf(d)
  );

  const priorityOrdinals = [
    {
      words: [
        "first",
        "1st",
        "الاول",
        "الأول",
        "اول",
        "أول",
        "الاولى",
        "الأولى",
        "اولى",
        "أولى",
      ],
      idx: 1,
    },
    {
      words: [
        "second",
        "2nd",
        "التاني",
        "الثاني",
        "تاني",
        "ثاني",
        "التانية",
        "الثانية",
        "تانية",
        "ثانية",
      ],
      idx: 2,
    },
    {
      words: [
        "third",
        "3rd",
        "التالت",
        "الثالث",
        "تالت",
        "ثالث",
        "التالتة",
        "الثالثة",
        "تالتة",
        "ثالثة",
      ],
      idx: 3,
    },
    {
      words: ["fourth", "4th", "الرابع", "رابع", "الرابعة", "رابعة"],
      idx: 4,
    },
    {
      words: ["fifth", "5th", "الخامس", "خامس", "الخامسة", "خامسة"],
      idx: 5,
    },
  ];

  for (const item of priorityOrdinals) {
    if (item.words.some((word) => normalized.includes(word))) {
      return item.idx;
    }
  }

  const digitMatch = normalized.match(
    /(?:#|number\s*|رقم\s*)?(\d+)/i
  );

  if (digitMatch) {
    return parseInt(digitMatch[1], 10);
  }

  const wordNumbers = [
    { words: ["one", "واحد"], idx: 1 },
    { words: ["two", "اتنين", "ثنين"], idx: 2 },
    { words: ["three", "تلاتة", "ثلاثة"], idx: 3 },
    { words: ["four", "اربعة", "أربعة"], idx: 4 },
    { words: ["five", "خمسة"], idx: 5 },
  ];

  for (const item of wordNumbers) {
    if (item.words.some((word) => normalized.includes(word))) {
      return item.idx;
    }
  }

  return null;
};

const isSelectionRequest = (value) => {
  const lo = value.toLowerCase();
  const idx = getSelectionIndex(lo);

  if (idx === null) return false;

  return (
    /\b(want|choose|pick|select|give|take|get|buy|order|number|no|#)\b/.test(
      lo
    ) ||
    /(عايز|عايزة|اختار|هاخد|هات|أول|اول|تاني|تالت|رقم|طلب|واحدة|واحد)/.test(
      lo
    ) ||
    /^\s*#?\d+\s*$/.test(lo) ||
    /\b(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th)\b/.test(lo)
  );
};

export default function Chat({ onReply }) {
  const [msgs, setMsgs] = useState([
    {
      from: "bot",
      text: "Hello! I am your AI spare-parts assistant. How can I help you today?",
    },
  ]);

  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingOrder, setPendingOrder] = useState(null);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [address, setAddress] = useState("");

  const box = useRef();
  const lastResults = useRef([]);

  useEffect(() => {
    if (box.current) {
      box.current.scrollTop = box.current.scrollHeight;
    }
  }, [msgs, busy]);

  const choosePayment = (method) => {
    if (!pendingOrder || busy) return;

    const paymentLabel =
      method === "visa" ? "Visa" : "Cash on Delivery";

    setSelectedPayment(method);

    setMsgs((p) => [
      ...p,
      {
        from: "me",
        text: paymentLabel,
      },
      {
        from: "bot",
        text:
          "Great! Now please enter your full delivery address.",
        addressInput: true,
      },
    ]);
  };

  const submitOrder = async () => {
    if (!pendingOrder || !selectedPayment || !address.trim() || busy) {
      return;
    }

    setBusy(true);

    try {
      const paymentLabel =
        selectedPayment === "visa"
          ? "Visa"
          : "Cash on Delivery";

      const { data } = await AgentAPI.message(
        `Order ${pendingOrder.title}`,
        {
          payment_method: selectedPayment,
          delivery_address: address.trim(),
        }
      );

      const reply =
        "Order request submitted! I've created an order for:\n\n" +
        `📦 ${pendingOrder.title}\n` +
        `Total: EGP ${pendingOrder.price}\n` +
        `Payment: ${paymentLabel}\n` +
        `📍 Delivery Address: ${address.trim()}\n\n` +
        `${data.reply}`;

      setMsgs((p) => [
        ...p,
        {
          from: "bot",
          text: reply,
        },
      ]);

      setPendingOrder(null);
      setSelectedPayment(null);
      setAddress("");

      onReply?.(data);
    } catch {
      setMsgs((p) => [
        ...p,
        {
          from: "bot",
          text:
            "An error occurred while creating your order. Please try again.",
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
      if (isStockRequest(m)) {
        lastResults.current = STOCK;

        const reply =
          "Here is our current inventory stock:\n\n" +
          STOCK.map(
            (p, i) =>
              `${i + 1}. ${p.title} — ${p.stock} units in stock — EGP ${p.price}`
          ).join("\n") +
          '\n\nReply with a number to place an order (e.g., "I want 1").';

        setMsgs((p) => [
          ...p,
          {
            from: "bot",
            text: reply,
          },
        ]);

        onReply?.({
          intent: "stock_check",
          items: STOCK,
        });
      } else if (isPartSearchRequest(m)) {
        const detectedBrand = detectBrand(m);

        let matches = [];

        if (detectedBrand) {
          matches = STOCK.filter(
            (p) => p.brand === detectedBrand
          );
        } else {
          const cleanQ = m
            .toLowerCase()
            .replace(/خيونداي/g, "هيونداي")
            .replace(/هيونداى/g, "هيونداي")
            .replace(/النترا/g, "إلنترا");

          const words = cleanQ
            .split(/\s+/)
            .filter(
              (w) => w.length >= 2 && !STOPWORDS.has(w)
            );

          matches = STOCK.filter((p) => {
            const titleLower = p.title.toLowerCase();
            const keys = p.keywords || [];

            return words.some(
              (w) =>
                titleLower.includes(w) ||
                keys.some(
                  (k) => k.includes(w) || w.includes(k)
                )
            );
          });
        }

        const results = matches.length ? matches : STOCK;

        lastResults.current = results;

        const reply = matches.length
          ? "I found these matching spare parts:\n\n" +
            results
              .map(
                (p, i) =>
                  `${i + 1}. ${p.title} — ${p.stock} units — EGP ${p.price}`
              )
              .join("\n") +
            '\n\nReply with a number to order (e.g. "I want 1").'
          : "I couldn't find an exact match, but here are our available spare parts:\n\n" +
            results
              .map(
                (p, i) =>
                  `${i + 1}. ${p.title} — ${p.stock} units — EGP ${p.price}`
              )
              .join("\n") +
            '\n\nReply with a number to order (e.g. "I want 1").';

        setMsgs((p) => [
          ...p,
          {
            from: "bot",
            text: reply,
          },
        ]);

        onReply?.({
          intent: "part_search",
          items: results,
        });
      } else if (isTrackingRequest(m)) {
        const { data: orders } = await TaskAPI.list();

        const active =
          orders.find((o) =>
            ["shipped", "processing", "pending_approval"].includes(
              o.status
            )
          ) || orders[0];

        const reply = active
          ? `Your latest active order is #${active.id} — ${active.title}.

Status: ${statusTextEn[active.status] || active.status}.

${
  active.location
    ? `Current location: ${active.location}.\n`
    : ""
}${
  active.eta && active.status !== "delivered"
    ? `Estimated arrival: ${active.eta}.`
    : ""
}`
          : "You do not have any active orders yet. Let me know if you would like to order spare parts!";

        setMsgs((p) => [
          ...p,
          {
            from: "bot",
            text: reply,
            tracking: active,
          },
        ]);

        onReply?.({
          intent: "track_order",
          order: active,
        });
      } else if (
        isSelectionRequest(m) &&
        lastResults.current.length > 0
      ) {
        const idx = getSelectionIndex(m);

        if (
          idx &&
          idx >= 1 &&
          idx <= lastResults.current.length
        ) {
          const chosen = lastResults.current[idx - 1];

          setPendingOrder(chosen);

          setMsgs((p) => [
            ...p,
            {
              from: "bot",
              text:
                "You selected:\n\n" +
                `📦 ${chosen.title}\n` +
                `Total: EGP ${chosen.price}\n\n` +
                "How would you like to pay?",
              paymentOptions: true,
            },
          ]);
        } else {
          const reply =
            `Please choose a valid number between 1 and ` +
            `${lastResults.current.length}.`;

          setMsgs((p) => [
            ...p,
            {
              from: "bot",
              text: reply,
            },
          ]);
        }
      } else {
        const lo = m.toLowerCase();
        let reply;

        if (
          /^(hi|hello|hey|ازيك|مرحبا|سلام|أهلا|اهلا)/.test(
            lo
          )
        ) {
          reply =
            "Hello! How can I help you today? I can search for spare parts, check live stock, or track your orders.";
        } else if (
          /\b(thank|thanks|شكرا|شكراً|تسلم|حبيبي|تمام|ماشي)\b/.test(
            lo
          )
        ) {
          reply =
            "You're very welcome! Feel free to ask if you need any other assistance.";
        } else if (
          /\b(order|buy|purchase|شراء|طلب|عايز اشتري)\b/.test(
            lo
          )
        ) {
          const { data } = await AgentAPI.message(m);

          setMsgs((p) => [
            ...p,
            {
              from: "bot",
              text: data.reply,
            },
          ]);

          onReply?.(data);

          setBusy(false);
          return;
        } else if (
          /\b(help|مساعدة|تقدر تعمل ايه|إيه)\b/.test(lo)
        ) {
          reply =
            "I can assist you with:\n\n" +
            "• Search spare parts by name or model\n" +
            "• Live stock & pricing availability\n" +
            "• Track your pending & active shipments\n" +
            "• Submit purchase orders for approval\n\n" +
            "What would you like to do?";
        } else {
          reply =
            'I am here to assist with your spare-parts workflows. Try asking:\n\n' +
            '• "Find brake pads for Hyundai Elantra"\n' +
            '• "What parts are in stock?"\n' +
            '• "Where is my order?"';
        }

        setMsgs((p) => [
          ...p,
          {
            from: "bot",
            text: reply,
          },
        ]);

        onReply?.({
          intent: "conversation",
        });
      }
    } catch {
      setMsgs((p) => [
        ...p,
        {
          from: "bot",
          text:
            "An error occurred while connecting to the assistant. Please try again.",
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
              {m.text}
            </div>

            {m.paymentOptions && (
              <div className="payment-options">
                <button
                  className="payment-btn"
                  onClick={() => choosePayment("cash")}
                  disabled={busy}
                >
                  💵 Cash on Delivery
                </button>

                <button
                  className="payment-btn"
                  onClick={() => choosePayment("visa")}
                  disabled={busy}
                >
                  💳 Visa
                </button>
              </div>
            )}

            {m.addressInput && (
              <div className="address-input-box">
                <textarea
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Enter your full delivery address..."
                  rows={3}
                  disabled={busy}
                />

                <button
                  className="address-submit-btn"
                  onClick={submitOrder}
                  disabled={busy || !address.trim()}
                >
                  {busy ? "Submitting..." : "Confirm Order"}
                </button>
              </div>
            )}

            {m.tracking && (
              <div className="tracking-mini">
                <div>
                  <b>Order #{m.tracking.id}</b>
                  <span>{m.tracking.title}</span>
                </div>

                <span
                  className={`status-pill ${m.tracking.status}`}
                >
                  {statusTextEn[m.tracking.status] ||
                    m.tracking.status.replace("_", " ")}
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

      <div className="chips">
        {[
          "What parts are in stock?",
          "Find brake pads for Hyundai Elantra",
          "Where is my order?",
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
          placeholder="Ask about spare parts, stock prices, or track orders..."
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