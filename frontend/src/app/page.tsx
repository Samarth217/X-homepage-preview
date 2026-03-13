import RefreshButton from "./refresh-button";

type ApiStoryPost = {
  id: number;
  author_handle: string;
  text: string;
  created_at: string;
};

type ApiStory = {
  id: number;
  headline: string;
  summary: string;
  category: string | null;
  story_score: number | null;
  created_at: string;
  updated_at: string;
  representative_posts: ApiStoryPost[];
};

type Story = {
  id: string;
  category: string;
  headline: string;
  summary: string;
  updatedAt: string; // ISO-like
  posts: { author: string; text: string }[];
};

async function fetchStories(): Promise<{ stories: Story[]; error: string | null }> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!base) {
    return { stories: [], error: "Missing NEXT_PUBLIC_API_BASE_URL." };
  }

  try {
    const url = `${base.replace(/\/$/, "")}/stories?limit=12`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      return { stories: [], error: `Failed to load stories (HTTP ${res.status}).` };
    }

    const data = (await res.json()) as ApiStory[];
    const stories: Story[] = (data ?? []).map((s) => ({
      id: String(s.id),
      category: s.category ?? "General",
      headline: s.headline,
      summary: s.summary,
      updatedAt: s.updated_at ?? s.created_at,
      posts: (s.representative_posts ?? []).map((p) => ({
        author: p.author_handle,
        text: p.text,
      })),
    }));

    return { stories, error: null };
  } catch {
    return { stories: [], error: "Failed to load stories." };
  }
}

export default async function Home() {
  const { stories, error } = await fetchStories();
  const featured = stories[0] ?? null;
  const rest = featured ? stories.slice(1) : [];

  const formatUpdated = (iso: string) => {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "Updated recently";
    return `Updated ${d.toLocaleString(undefined, {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  };

  const StoryCard = ({ story }: { story: Story }) => (
    <article className="group flex h-full flex-col rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-center justify-between gap-4">
        <span className="inline-flex items-center rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs font-medium text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
          {story.category}
        </span>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          {formatUpdated(story.updatedAt)}
        </span>
      </div>

      <h3 className="mt-4 text-lg font-semibold leading-snug tracking-tight text-zinc-950 dark:text-zinc-50">
        {story.headline}
      </h3>
      <p className="mt-2 line-clamp-3 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
        {story.summary}
      </p>

      <div className="mt-5 space-y-2">
        {story.posts.slice(0, 4).map((p, idx) => (
          <div
            key={`${story.id}-${idx}`}
            className="rounded-xl border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm leading-6 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200"
          >
            <span className="font-semibold text-zinc-900 dark:text-zinc-50">
              @{p.author}
            </span>{" "}
            <span className="text-zinc-700 dark:text-zinc-200">{p.text}</span>
          </div>
        ))}
      </div>

      <div className="mt-auto pt-6">
        <div className="inline-flex items-center gap-2 text-sm font-medium text-zinc-900 dark:text-zinc-50">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
          Read story
          <span className="ml-1 text-zinc-400 transition-transform group-hover:translate-x-0.5">
            →
          </span>
        </div>
      </div>
    </article>
  );

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[520px] bg-gradient-to-b from-blue-50 via-zinc-50 to-transparent dark:from-blue-950/40 dark:via-black dark:to-transparent" />

      <header className="sticky top-0 z-20 border-b border-zinc-200 bg-zinc-50/80 backdrop-blur dark:border-zinc-800 dark:bg-black/60">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-950 text-sm font-bold text-white dark:bg-white dark:text-black">
              X
            </div>
            <div className="leading-tight">
              <div className="text-sm font-semibold tracking-tight">X Stories</div>
              <div className="text-xs text-zinc-500 dark:text-zinc-400">
                Logged-out front page
              </div>
            </div>
          </div>

          <nav className="hidden items-center gap-6 text-sm text-zinc-600 dark:text-zinc-300 md:flex">
            <a className="hover:text-zinc-950 dark:hover:text-white" href="#">
              Top
            </a>
            <a className="hover:text-zinc-950 dark:hover:text-white" href="#">
              Technology
            </a>
            <a className="hover:text-zinc-950 dark:hover:text-white" href="#">
              Markets
            </a>
            <a className="hover:text-zinc-950 dark:hover:text-white" href="#">
              Culture
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <a
              href="#"
              className="hidden rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-900 shadow-sm hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-50 dark:hover:bg-zinc-900 md:inline-flex"
            >
              Sign in
            </a>
            <a
              href="#"
              className="inline-flex rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
            >
              Create account
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-6 pb-16 pt-10">
        <section className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-8">
            <div className="rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <div className="flex flex-wrap items-center gap-3">
                <span className="inline-flex items-center rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">
                  Featured
                </span>
                {featured ? (
                  <>
                    <span className="inline-flex items-center rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs font-medium text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
                      {featured.category}
                    </span>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {formatUpdated(featured.updatedAt)}
                    </span>
                  </>
                ) : (
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {error ? "Unable to load stories" : "No stories yet"}
                  </span>
                )}
              </div>

              <h1 className="mt-5 text-3xl font-semibold leading-tight tracking-tight text-zinc-950 dark:text-white">
                {featured ? featured.headline : error ? "Stories unavailable" : "No stories yet"}
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-600 dark:text-zinc-300">
                {featured
                  ? featured.summary
                  : error
                    ? "We couldn’t fetch stories from the backend. Make sure the API is running and `NEXT_PUBLIC_API_BASE_URL` is set."
                    : "Run the backend refresh once to generate stories, then reload this page."}
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {featured ? (
                  featured.posts.slice(0, 4).map((p, idx) => (
                    <div
                      key={`featured-${idx}`}
                      className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4 text-sm leading-6 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200"
                    >
                      <div className="font-semibold text-zinc-900 dark:text-zinc-50">
                        @{p.author}
                      </div>
                      <div className="mt-1">{p.text}</div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4 text-sm leading-6 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 sm:col-span-2">
                    {error ?? "No representative posts to show yet."}
                  </div>
                )}
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                <a
                  href="#"
                  className="inline-flex items-center justify-center rounded-full bg-zinc-950 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
                >
                  Read the full story
                </a>
                <div className="text-xs text-zinc-500 dark:text-zinc-400">
                  {featured ? "Live stories, updated as conversations evolve." : "Connect the backend and refresh to populate stories."}
                </div>
              </div>
            </div>
          </div>

          <aside className="lg:col-span-4">
            <div className="h-full rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <div className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">
                Today’s brief
              </div>
              <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                A clean, logged-out front page inspired by X—stories first, posts as receipts.
              </p>
              <div className="mt-6 space-y-3">
                {rest.slice(0, 3).map((s) => (
                  <a
                    key={s.id}
                    href="#"
                    className="block rounded-2xl border border-zinc-200 bg-zinc-50 p-4 transition hover:bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:bg-zinc-800"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs font-medium text-zinc-600 dark:text-zinc-300">
                        {s.category}
                      </span>
                      <span className="text-xs text-zinc-500 dark:text-zinc-400">
                        {formatUpdated(s.updatedAt)}
                      </span>
                    </div>
                    <div className="mt-2 line-clamp-2 text-sm font-semibold leading-6 text-zinc-950 dark:text-zinc-50">
                      {s.headline}
                    </div>
                  </a>
                ))}
                {!featured && (
                  <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4 text-sm leading-6 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
                    {error ?? "No stories to brief yet."}
                  </div>
                )}
              </div>
            </div>
          </aside>
        </section>

        <section className="mt-10">
          <div className="flex items-end justify-between gap-6">
            <div>
              <h2 className="text-lg font-semibold tracking-tight text-zinc-950 dark:text-white">
                Stories
              </h2>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                Clusters of public posts, distilled into headlines.
              </p>
            </div>
            <div className="flex items-center gap-4">
  <div className="hidden text-xs text-zinc-500 dark:text-zinc-400 md:block">
    Desktop-first layout · no sign-in required
  </div>
  <RefreshButton />
</div>
          </div>

          <div className="mt-6 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {rest.map((s) => (
              <StoryCard key={s.id} story={s} />
            ))}
            {!featured && (
              <div className="rounded-2xl border border-zinc-200 bg-white p-6 text-sm leading-6 text-zinc-600 shadow-sm dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300 md:col-span-2 xl:col-span-3">
                <div className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">
                  {error ? "Couldn’t load stories" : "No stories yet"}
                </div>
                <div className="mt-2">
                  {error
                    ? "Check that the FastAPI server is running and that CORS/networking allows requests from the frontend."
                    : "Run `POST /refresh` on the backend once, then reload this page."}
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="mt-12">
          <div className="rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
            <div className="grid gap-8 md:grid-cols-12 md:items-center">
              <div className="md:col-span-7">
                <h3 className="text-xl font-semibold tracking-tight text-zinc-950 dark:text-white">
                  Sign in to follow stories you care about
                </h3>
                <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                  Follow developing stories, join conversations, and explore what’s happening right now.
                </p>
              </div>
              <div className="md:col-span-5 md:flex md:justify-end">
                <div className="flex flex-col gap-3 sm:flex-row">
                  <a
                    href="#"
                    className="inline-flex items-center justify-center rounded-full border border-zinc-200 bg-white px-5 py-2.5 text-sm font-semibold text-zinc-900 shadow-sm hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-50 dark:hover:bg-zinc-900"
                  >
                    Sign in
                  </a>
                  <a
                    href="#"
                    className="inline-flex items-center justify-center rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
                  >
                    Create account
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        <footer className="mt-10 flex flex-col items-start justify-between gap-3 border-t border-zinc-200 pt-6 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400 md:flex-row md:items-center">
          <div>© {new Date().getFullYear()} X Stories</div>
          <div>Desktop-first · Stories updated throughout the day</div>        </footer>
      </main>
    </div>
  );
  
}
