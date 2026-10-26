import { SearchWorkspace } from "@/components/search-workspace";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q = "" } = await searchParams;
  return <SearchWorkspace initialQuery={q} />;
}
