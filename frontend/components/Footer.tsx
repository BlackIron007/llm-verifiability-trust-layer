export default function Footer() {
  return (
    <footer className="border-t border-border py-12 mt-24">
      <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-sm text-textSecondary font-light">
          Built with transparency in mind
        </p>
        <p className="text-xs text-textSecondary/60 font-light">
          Open-source AI verification middleware
        </p>
      </div>
    </footer>
  );
}
