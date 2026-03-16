import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { DynamicCodeBlock } from "@/components/DynamicCodeBlock";
import { UseWith } from "@/components/UseWith";
import { Features } from "@/components/Features";
import { CTA } from "@/components/CTA";
import { Footer } from "@/components/Footer";
import { CursorBackground } from "@/components/CursorBackground";

export default function Home() {
  return (
    <main className="bg-hero overflow-x-hidden min-h-screen relative">
      <CursorBackground />
      <div className="relative z-10">
        <Header />
        <Hero />
        <DynamicCodeBlock />
        <UseWith />
        <Features />
        <CTA />
        <Footer />
      </div>
    </main>
  );
}
