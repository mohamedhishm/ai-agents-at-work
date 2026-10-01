const wait = (d) => new Promise((r) => setTimeout(() => r({ data: d }), 350));

const seedUsers = {
  "salma@eldoctor.com": { id: 2, name: "Salma Mohamed", email: "salma@eldoctor.com", password: "demo1234", role: "customer" },
  "salma@orbit.com": { id: 2, name: "Salma Mohamed", email: "salma@orbit.com", password: "demo1234", role: "customer" },
  "nour@eldoctor.com": { id: 1, name: "Nour Hussien", email: "nour@eldoctor.com", password: "demo1234", role: "admin" },
  "nour@orbit.com": { id: 1, name: "Nour Hussien", email: "nour@orbit.com", password: "demo1234", role: "admin" },
};

const getUsers = () => {
  if (typeof window === "undefined") return seedUsers;
  const saved = JSON.parse(localStorage.getItem("eldoctor_users") || "null");
  if (!saved) {
    localStorage.setItem("eldoctor_users", JSON.stringify(seedUsers));
    return seedUsers;
  }
  const merged = { ...seedUsers, ...saved };
  localStorage.setItem("eldoctor_users", JSON.stringify(merged));
  return merged;
};
const publicUser = ({ password, ...user }) => user;
const currentEmail = () => {
  if (typeof window === "undefined") return "salma@eldoctor.com";
  const token = localStorage.getItem("token") || "";
  if (token.startsWith("mock-user:")) return decodeURIComponent(token.slice("mock-user:".length));
  return "";
};
const currentUser = () => {
  const users = getUsers();
  const email = currentEmail();
  if (email && users[email]) return users[email];
  const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";
  if (token === "mock-admin") return users["nour@eldoctor.com"];
  if (token === "mock-customer") return users["salma@eldoctor.com"];
  return null;
};
const role = () => currentUser()?.role || "customer";

let orders = [
  { id: 1042, title: "Hyundai Elantra Front Brake Pads", customer: "Salma Mohamed", amount: 189, status: "shipped", eta: "Tomorrow", location: "El Doctor warehouse — Alexandria" },
  { id: 1043, title: "Kia Cerato Oil Filter", customer: "Salma Mohamed", amount: 420, status: "pending_approval", eta: "After approval", location: "Human approval queue" },
  { id: 1044, title: "Chevrolet Aveo Air Filter", customer: "Omar Hassan", amount: 59, status: "processing", eta: "Oct 2", location: "El Doctor main warehouse" },
  { id: 1045, title: "Nissan Sunny Spark Plugs", customer: "Omar Hassan", amount: 95, status: "delivered", eta: "Delivered", location: "Delivered to customer" },
  { id: 1046, title: "Kia Sportage Brake Disc", customer: "Salma Mohamed", amount: 140, status: "delivered", eta: "Delivered", location: "Delivered to customer" },
];

let activity = [
  { id: 1, type: "Tool call", detail: "Checked stock for Kia Cerato Oil Filter", status: "done" },
  { id: 2, type: "RAG lookup", detail: "Retrieved warranty policy for order #1043", status: "done" },
  { id: 3, type: "Approval", detail: "Order #1043 needs human approval (over $400)", status: "pending_approval" },
];

export const mock = {
  login: ({ email, password }) => {
    const users = getUsers();
    const found = users[(email || "").trim().toLowerCase()];
    if (!found || found.password !== password) return Promise.reject(new Error("Invalid email or password."));
    return wait({ token: `mock-user:${encodeURIComponent(found.email)}`, user: publicUser(found) });
  },
  register: ({ name, email, password }) => {
    const users = getUsers();
    const key = email.trim().toLowerCase();
    if (users[key]) return Promise.reject(new Error("An account with this email already exists."));
    const user = { id: Date.now(), name: name.trim(), email: key, password, role: "customer" };
    users[key] = user;
    localStorage.setItem("eldoctor_users", JSON.stringify(users));
    return wait({ token: `mock-user:${encodeURIComponent(user.email)}`, user: publicUser(user) });
  },
  me: () => {
    const user = currentUser();
    return wait(user ? publicUser(user) : null);
  },
  list: () => {
    const users = getUsers();
    const current = Object.values(users).find((u) => u.role === role());
    return wait(role() === "admin" ? orders : orders.filter((o) => o.customer === (current?.name || "Salma Mohamed")));
  },
  activity: () => wait(activity),
  approve: (id, ok) => {
    orders = orders.map((o) => (o.id === id ? { ...o, status: ok ? "processing" : "rejected", location: ok ? "El Doctor main warehouse" : "Human approval" } : o));
    activity = [{ id: Date.now(), type: "Approval", detail: `Order #${id} ${ok ? "approved" : "rejected"} by admin`, status: "done" }, ...activity];
    return wait({});
  },
  message: (text) => {
    const input = (text || "").trim();
    const id = 1047 + orders.length;
    orders = [{ id, title: input.replace(/^Order\s+/i, "") || "Spare-parts request", customer: "Salma Mohamed", amount: 189, status: "pending_approval", eta: "After approval", location: "Human approval queue" }, ...orders];
    activity = [{ id: Date.now(), type: "Task created", detail: `New spare-parts request #${id} from chat`, status: "pending_approval" }, ...activity];
    return wait({ reply: `Request #${id} has been created and sent for administrator approval.`, status: "pending_approval", intent: "new_request" });
  },
};
