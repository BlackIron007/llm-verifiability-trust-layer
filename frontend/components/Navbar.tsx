"use client";

import { useState, useEffect } from "react";

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-background/90 backdrop-blur-md border-b border-border shadow-sm"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
        <button
          onClick={() => scrollTo("hero")}
          className="text-base font-medium tracking-tight text-primary"
        >
          Veritas AI
        </button>

        <div className="flex items-center gap-8">
          {[
            { label: "How It Works", id: "how-it-works" },
            { label: "Features", id: "features" },
            { label: "FAQ", id: "faq" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="text-sm text-textSecondary hover:text-primary transition-colors duration-200"
            >
              {item.label}
            </button>
          ))}
          <button
            onClick={() => scrollTo("demo")}
            className="text-sm text-background bg-primary px-4 py-1.5 rounded hover:bg-secondary transition-colors duration-200"
          >
            Try It Live
          </button>
        </div>
      </div>
    </nav>
  );
}
