export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6">
      <h1 className="text-4xl font-bold text-text-primary">
        Intelligence Hub
      </h1>
      <p className="mt-4 max-w-xl text-center text-lg text-text-secondary">
        Welcome to IntelPolitics — your command center for political
        accountability intelligence. Track truthfulness, compare records, and
        access comprehensive politician dossiers.
      </p>
      <div className="mt-8 flex gap-4">
        <a
          href="/dossier"
          className="rounded-lg bg-accent px-5 py-2.5 font-medium text-background transition-colors hover:bg-accent-hover"
        >
          Dossiers
        </a>
        <a
          href="/truthfulness"
          className="rounded-lg border border-accent/30 px-5 py-2.5 font-medium text-accent transition-colors hover:border-accent"
        >
          Truthfulness
        </a>
      </div>
    </main>
  );
}
