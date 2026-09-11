"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";
const PROJECT_ID = "3e0b5e1f-a2bc-4937-a4f6-9f47d8960a96";

type Project = {
  id: string;
  name?: string;
  description?: string;
  created_at?: string;
};

type Dataset = {
  id: string;
  name?: string;
  source?: string;
  record_count?: number;
  created_at?: string;
  status?: string;
};

type DatasetVersion = {
  id: string;
  dataset_id?: string;
  version?: number;
  record_count?: number;
  storage_path?: string;
  created_at?: string;
  status?: string;
};

type Analysis = {
  id: string;
  project_id?: string;
  dataset_version_id?: string;
  analysis_type?: string;
  capability_id?: string;
  name?: string;
  status?: string;
  created_at?: string;
  result?: unknown;
};

type CapabilityProvider = {
  name?: string;
  package?: string;
  version?: string;
  capability?: string;
  priority?: number;
  available?: boolean;
  metadata?: Record<string, unknown>;
};

type Capability = {
  name: string;
  providers?: CapabilityProvider[];
};

type CapabilitiesResponse = {
  capabilities?: Capability[];
};

type DashboardResponse = {
  project?: Project;
  datasets?: Dataset[];
  analyses?: Analysis[];
  [key: string]: unknown;
};

type ResultRecord = Record<string, unknown>;

const CAPABILITY_LABELS: Record<string, string> = {
  "document.count": "Document Count",
  "publication.year_distribution": "Publication Growth",
  "author.productivity": "Author Productivity",
  "citation.total": "Total Citations",
  "citation.average": "Average Citations",
  "citation.distribution": "Citation Distribution",
  "source.productivity": "Source Productivity",
  "keyword.frequency": "Keyword Frequency",
  "author.co_authorship": "Co-authorship Network",
  "citation.author_h_index": "Author H-index",
};

function title(value?: string) {
  if (!value) return "Analysis";

  return value
    .split(".")
    .map((part) =>
      part
        .replace(/_/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase())
    )
    .join(" · ");
}

function capabilityLabel(name?: string) {
  return name ? CAPABILITY_LABELS[name] || title(name) : "Analysis";
}

function formatNumber(value?: number | null) {
  return value === undefined || value === null
    ? "—"
    : new Intl.NumberFormat("en-US").format(value);
}

function formatDate(value?: string) {
  if (!value) return "—";

  try {
    return new Date(value).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return value;
  }
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "—";

  if (typeof value === "number") {
    return new Intl.NumberFormat("en-US", {
      maximumFractionDigits: 4,
    }).format(value);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "string") {
    return value;
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function extractResultPayload(result: unknown): {
  scalarEntries: Array<[string, unknown]>;
  records: ResultRecord[];
  metadata: Array<[string, unknown]>;
} {
  if (!result || typeof result !== "object") {
    return {
      scalarEntries: [],
      records: [],
      metadata: [],
    };
  }

  const root = result as Record<string, unknown>;

  const scalarEntries: Array<[string, unknown]> = [];
  const metadata: Array<[string, unknown]> = [];

  const rawRecords = root.records;

  const records = Array.isArray(rawRecords)
    ? rawRecords.filter(
        (x): x is ResultRecord =>
          !!x && typeof x === "object" && !Array.isArray(x)
      )
    : [];

  for (const [key, value] of Object.entries(root)) {
    if (key === "records" || key === "parameters") continue;

    if (
      value === null ||
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ) {
      scalarEntries.push([key, value]);
    } else {
      metadata.push([key, value]);
    }
  }

  return {
    scalarEntries,
    records,
    metadata,
  };
}

function recordColumns(records: ResultRecord[]): string[] {
  const keys: string[] = [];

  for (const record of records.slice(0, 100)) {
    for (const key of Object.keys(record)) {
      if (!keys.includes(key)) {
        keys.push(key);
      }
    }
  }

  const preferred = [
    "year",
    "author",
    "h_index",
    "source",
    "journal",
    "keyword",
    "term",
    "count",
    "citations",
    "citation_count",
    "frequency",
    "coauthor",
    "co_author",
    "value",
    "documents",
    "document_count",
  ];

  return [
    ...preferred.filter((x) => keys.includes(x)),
    ...keys.filter((x) => !preferred.includes(x)),
  ];
}

function sortRecords(
  records: ResultRecord[],
  analysisType?: string
): ResultRecord[] {
  return [...records].sort((a, b) => {
    const numericKeys = [
      "h_index",
      "count",
      "citations",
      "citation_count",
      "frequency",
      "value",
      "documents",
      "document_count",
    ];

    for (const key of numericKeys) {
      const av = Number(a[key]);
      const bv = Number(b[key]);

      if (
        Number.isFinite(av) &&
        Number.isFinite(bv) &&
        av !== bv
      ) {
        return bv - av;
      }
    }

    if (analysisType === "publication.year_distribution") {
      return String(a.year ?? "").localeCompare(
        String(b.year ?? "")
      );
    }

    return 0;
  });
}

export default function Home() {
  const [dashboard, setDashboard] =
    useState<DashboardResponse | null>(null);

  const [capabilities, setCapabilities] =
    useState<Capability[]>([]);

  const [versions, setVersions] =
    useState<DatasetVersion[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [modal, setModal] =
    useState<"analysis" | "upload" | null>(null);

  const [selectedCapability, setSelectedCapability] =
    useState("");

  const [selectedDatasetId, setSelectedDatasetId] =
    useState("");

  const [selectedVersionId, setSelectedVersionId] =
    useState("");

  const [running, setRunning] =
    useState(false);

  const [uploading, setUploading] =
    useState(false);

  const [selectedAnalysis, setSelectedAnalysis] =
    useState<Analysis | null>(null);

  const [message, setMessage] =
    useState("");

  const [datasetName, setDatasetName] =
    useState("");

  const [datasetSource, setDatasetSource] =
    useState("Scopus");

  const [datasetFile, setDatasetFile] =
    useState<File | null>(null);

  const project = dashboard?.project;

  const datasets = useMemo(
    () => dashboard?.datasets || [],
    [dashboard]
  );

  const analyses = useMemo(
    () => dashboard?.analyses || [],
    [dashboard]
  );

  const selectedDataset = useMemo(
    () =>
      datasets.find(
        (x) => x.id === selectedDatasetId
      ),
    [datasets, selectedDatasetId]
  );

  const selectedVersion = useMemo(
    () =>
      versions.find(
        (x) => x.id === selectedVersionId
      ),
    [versions, selectedVersionId]
  );

  const documents = useMemo(
    () =>
      datasets.reduce(
        (sum, dataset) =>
          sum + (dataset.record_count || 0),
        0
      ),
    [datasets]
  );

  const coverageCount = capabilities.length;

  const has = (name: string) =>
    capabilities.some(
      (x) => x.name === name
    );

  const hasGrowthCapability = has(
    "publication.year_distribution"
  );

  const hasAuthorCapability = has(
    "author.productivity"
  );

  const hasCitationCapability = has(
    "citation.total"
  );

  const hasKeywordCapability = has(
    "keyword.frequency"
  );

  async function loadDashboard() {
    try {
      setLoading(true);

      const [
        dashboardRes,
        capabilityRes,
      ] = await Promise.all([
        fetch(
          `${API_BASE_URL}/projects/${PROJECT_ID}/dashboard`
        ),
        fetch(
          `${API_BASE_URL}/analysis/capabilities`
        ),
      ]);

      if (!dashboardRes.ok) {
        throw new Error(
          `Dashboard request failed: ${dashboardRes.status}`
        );
      }

      const dashboardData: DashboardResponse =
        await dashboardRes.json();

      setDashboard(dashboardData);

      if (capabilityRes.ok) {
        const capabilityData: CapabilitiesResponse =
          await capabilityRes.json();

        setCapabilities(
          capabilityData.capabilities || []
        );
      } else {
        setCapabilities([]);
      }
    } catch (error) {
      console.error(error);

      setMessage(
        "Unable to connect to SciAI backend."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadVersions(datasetId: string) {
    if (!datasetId) {
      setVersions([]);
      setSelectedVersionId("");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/datasets/${datasetId}/versions`
      );

      if (!response.ok) {
        throw new Error(
          `Versions request failed: ${response.status}`
        );
      }

      const data = await response.json();

      const list: DatasetVersion[] =
        Array.isArray(data)
          ? data
          : data.versions ||
            data.items ||
            [];

      setVersions(list);

      setSelectedVersionId((current) =>
        current &&
        list.some((x) => x.id === current)
          ? current
          : list[0]?.id || ""
      );
    } catch (error) {
      console.error(error);

      setVersions([]);
      setSelectedVersionId("");

      setMessage(
        "Unable to load dataset versions."
      );
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (
      !selectedDatasetId &&
      datasets.length
    ) {
      setSelectedDatasetId(
        datasets[0].id
      );
    }
  }, [datasets, selectedDatasetId]);

  useEffect(() => {
    if (selectedDatasetId) {
      loadVersions(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  useEffect(() => {
    if (!capabilities.length) return;

    setSelectedCapability((current) =>
      current &&
      capabilities.some(
        (x) => x.name === current
      )
        ? current
        : capabilities.find(
            (x) =>
              x.name ===
              "publication.year_distribution"
          )?.name ||
          capabilities[0].name
    );
  }, [capabilities]);

  function openAnalysisModal() {
    setMessage("");

    if (
      datasets.length &&
      !selectedDatasetId
    ) {
      setSelectedDatasetId(
        datasets[0].id
      );
    }

    setModal("analysis");
  }

  function selectCapability(name: string) {
    setSelectedCapability(name);
  }

  /*
   * Load the actual records for an analysis.
   *
   * The dashboard endpoint only returns analysis metadata.
   * Therefore previous analyses must use:
   *
   * GET /analysis/{analysis_id}/records
   */
  async function loadAnalysisResult(
    analysis: Analysis
  ) {
    try {
      setMessage("");

      const response = await fetch(
        `${API_BASE_URL}/analysis/${analysis.id}/records`
      );

      const data = await response
        .json()
        .catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `HTTP ${response.status}`
        );
      }

      setSelectedAnalysis({
        ...analysis,
        status:
          data?.status ||
          analysis.status ||
          "completed",
        analysis_type:
          analysis.analysis_type ||
          analysis.capability_id,
        result: data,
      });
    } catch (error) {
      console.error(error);

      setMessage(
        `Unable to load analysis result: ${
          error instanceof Error
            ? error.message
            : "Unknown error"
        }`
      );
    }
  }

  async function runAnalysis() {
    if (!selectedCapability) {
      return setMessage(
        "Please select an analysis capability."
      );
    }

    if (!selectedDatasetId) {
      return setMessage(
        "Please select a dataset."
      );
    }

    if (!selectedVersionId) {
      return setMessage(
        "Please select a dataset version."
      );
    }

    try {
      setRunning(true);
      setMessage("");

      /*
       * Step 1:
       * Create analysis
       */
      const createResponse = await fetch(
        `${API_BASE_URL}/analysis`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            project_id: PROJECT_ID,
            dataset_version_id:
              selectedVersionId,
            analysis_type:
              selectedCapability,
            parameters: {},
          }),
        }
      );

      const createdData =
        await createResponse
          .json()
          .catch(() => null);

      if (!createResponse.ok) {
        throw new Error(
          createdData?.detail ||
            createdData?.message ||
            `HTTP ${createResponse.status}`
        );
      }

      const analysisId =
        createdData?.id ||
        createdData?.analysis_id ||
        createdData?.analysis?.id;

      if (!analysisId) {
        throw new Error(
          "Analysis was created but no analysis ID was returned."
        );
      }

      /*
       * Step 2:
       * Run analysis
       */
      const runResponse = await fetch(
        `${API_BASE_URL}/analysis/run`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            analysis_id: analysisId,
          }),
        }
      );

      const runData =
        await runResponse
          .json()
          .catch(() => null);

      if (!runResponse.ok) {
        throw new Error(
          runData?.detail ||
            runData?.message ||
            `HTTP ${runResponse.status}`
        );
      }

      /*
       * Step 3:
       * Build analysis metadata
       */
      const analysis: Analysis = {
        id: analysisId,
        project_id: PROJECT_ID,
        dataset_version_id:
          selectedVersionId,
        analysis_type:
          runData?.analysis_type ||
          selectedCapability,
        capability_id:
          selectedCapability,
        status:
          runData?.status ||
          "completed",
        created_at:
          new Date().toISOString(),
        result: null,
      };

      /*
       * Step 4:
       * Load actual result records
       */
      await loadAnalysisResult(
        analysis
      );

      setMessage(
        "Analysis completed successfully."
      );

      setModal(null);

      /*
       * Step 5:
       * Refresh dashboard
       */
      await loadDashboard();
    } catch (error) {
      console.error(error);

      setMessage(
        `Analysis could not be completed: ${
          error instanceof Error
            ? error.message
            : "Unknown error"
        }`
      );
    } finally {
      setRunning(false);
    }
  }

  async function uploadDataset() {
    if (!datasetFile) {
      return setMessage(
        "Please select a dataset file."
      );
    }

    if (!datasetName.trim()) {
      return setMessage(
        "Please enter a dataset name."
      );
    }

    try {
      setUploading(true);
      setMessage("");

      const formData = new FormData();

      formData.append(
        "project_id",
        PROJECT_ID
      );

      formData.append(
        "name",
        datasetName.trim()
      );

      formData.append(
        "source",
        datasetSource
      );

      formData.append(
        "record_count",
        "0"
      );

      formData.append(
        "file",
        datasetFile
      );

      const response = await fetch(
        `${API_BASE_URL}/datasets/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data =
        await response
          .json()
          .catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `HTTP ${response.status}`
        );
      }

      setDatasetName("");
      setDatasetSource("Scopus");
      setDatasetFile(null);

      setMessage(
        "Dataset uploaded successfully."
      );

      setModal(null);

      await loadDashboard();
    } catch (error) {
      console.error(error);

      setMessage(
        `Dataset upload failed: ${
          error instanceof Error
            ? error.message
            : "Unknown error"
        }`
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <div className="flex min-h-screen">

        <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
          <div className="border-b border-slate-200 px-6 py-6">
            <div className="text-lg font-black tracking-tight">
              SciAI
            </div>

            <div className="mt-1 text-xs text-slate-400">
              Research Intelligence
            </div>
          </div>

          <nav className="flex-1 space-y-1 px-4 py-5">
            <SidebarItem
              label="Overview"
              active
            />
            <SidebarItem label="Datasets" />
            <SidebarItem label="Analyses" />
            <SidebarItem label="Authors" />
            <SidebarItem label="Sources" />
            <SidebarItem label="Keywords" />
            <SidebarItem label="Collaboration" />
          </nav>

          <div className="border-t border-slate-200 p-4">
            <div className="rounded-xl bg-slate-50 p-4">
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Workspace
              </div>

              <div className="mt-2 truncate text-sm font-bold">
                {project?.name ||
                  "Research Workspace"}
              </div>

              <div className="mt-1 text-xs text-slate-400">
                SciAI Project
              </div>
            </div>
          </div>
        </aside>

        <div className="w-full lg:pl-64">

          <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
            <div className="flex h-16 items-center justify-between px-5 sm:px-8">

              <div>
                <div className="text-xs font-semibold text-slate-400">
                  Research Intelligence
                </div>

                <div className="text-sm font-bold">
                  Research Overview
                </div>
              </div>

              <div className="flex items-center gap-2">

                <button
                  type="button"
                  onClick={() =>
                    loadDashboard()
                  }
                  className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold transition hover:bg-slate-50"
                >
                  Refresh
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setMessage("");
                    setModal("upload");
                  }}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold transition hover:bg-slate-50"
                >
                  Upload Dataset
                </button>

                <button
                  type="button"
                  onClick={openAnalysisModal}
                  className="rounded-lg bg-slate-950 px-4 py-2 text-xs font-bold text-white transition hover:bg-slate-800"
                >
                  Run Analysis
                </button>

              </div>
            </div>
          </header>

          <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">

            {message && (
              <div className="mb-6 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700">
                {message}
              </div>
            )}

            <section>
              <div className="max-w-3xl">

                <div className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                  Research Intelligence
                </div>

                <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                  Research Overview
                </h1>

                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">
                  Explore publication growth, authors,
                  citations, keywords, sources, and
                  collaboration patterns from your
                  research datasets.
                </p>

              </div>
            </section>

            <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

              <MetricCard
                label="Datasets"
                value={formatNumber(
                  datasets.length
                )}
                description="Research datasets"
                loading={loading}
              />

              <MetricCard
                label="Documents"
                value={formatNumber(
                  documents
                )}
                description="Indexed records"
                loading={loading}
              />

              <MetricCard
                label="Analyses"
                value={formatNumber(
                  analyses.length
                )}
                description="Created analyses"
                loading={loading}
              />

              <MetricCard
                label="Capabilities"
                value={formatNumber(
                  coverageCount
                )}
                description="Available analytical methods"
                loading={loading}
              />

            </section>

            <section className="mt-8 grid gap-6 xl:grid-cols-3">

              <div className="rounded-2xl border border-slate-200 bg-white p-6 xl:col-span-2">

                <SectionHeader
                  title="Research Growth"
                  description="Publication activity across time"
                />

                {hasGrowthCapability ? (
                  <EmptyState
                    title="Publication Growth"
                    description="Run the Publication Growth analysis to populate the result table below."
                    action="Run Publication Growth"
                    onAction={() => {
                      setSelectedCapability(
                        "publication.year_distribution"
                      );
                      setModal("analysis");
                    }}
                  />
                ) : (
                  <EmptyState
                    title="Growth analysis unavailable"
                    description="The publication year distribution capability is not currently registered."
                  />
                )}

              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6">

                <SectionHeader
                  title="Analytical Coverage"
                  description="Registered capabilities"
                />

                <div className="mt-5 space-y-3">

                  <Coverage
                    label="Publication Growth"
                    available={
                      hasGrowthCapability
                    }
                  />

                  <Coverage
                    label="Author Productivity"
                    available={
                      hasAuthorCapability
                    }
                  />

                  <Coverage
                    label="Citation Analysis"
                    available={
                      hasCitationCapability
                    }
                  />

                  <Coverage
                    label="Keyword Analysis"
                    available={
                      hasKeywordCapability
                    }
                  />

                  <Coverage
                    label="Source Productivity"
                    available={has(
                      "source.productivity"
                    )}
                  />

                  <Coverage
                    label="Co-authorship"
                    available={has(
                      "author.co_authorship"
                    )}
                  />

                  <Coverage
                    label="Author H-index"
                    available={has(
                      "citation.author_h_index"
                    )}
                  />

                </div>
              </div>

            </section>

            <section className="mt-8">

              <SectionHeader
                title="Research Landscape"
                description="Quick access to core scientometric analyses"
              />

              <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

                <QuickCard
                  title="Publication Growth"
                  description="Analyze publication activity by year."
                  available={
                    hasGrowthCapability
                  }
                  onClick={() => {
                    setSelectedCapability(
                      "publication.year_distribution"
                    );
                    setModal("analysis");
                  }}
                />

                <QuickCard
                  title="Author Productivity"
                  description="Explore the productivity of contributing authors."
                  available={
                    hasAuthorCapability
                  }
                  onClick={() => {
                    setSelectedCapability(
                      "author.productivity"
                    );
                    setModal("analysis");
                  }}
                />

                <QuickCard
                  title="Citation Analysis"
                  description="Analyze total, average, and citation distribution."
                  available={
                    hasCitationCapability
                  }
                  onClick={() => {
                    setSelectedCapability(
                      "citation.total"
                    );
                    setModal("analysis");
                  }}
                />

                <QuickCard
                  title="Keyword Analysis"
                  description="Identify frequently occurring research keywords."
                  available={
                    hasKeywordCapability
                  }
                  onClick={() => {
                    setSelectedCapability(
                      "keyword.frequency"
                    );
                    setModal("analysis");
                  }}
                />

              </div>
            </section>

            <section className="mt-8 grid gap-6 xl:grid-cols-2">

              <div className="rounded-2xl border border-slate-200 bg-white p-6">

                <SectionHeader
                  title="Collaboration Network"
                  description="Author co-authorship structure"
                />

                <EmptyState
                  title="Run co-authorship analysis"
                  description="The result will appear in the analysis results panel below."
                  action={
                    has(
                      "author.co_authorship"
                    )
                      ? "Run Co-authorship"
                      : undefined
                  }
                  onAction={
                    has(
                      "author.co_authorship"
                    )
                      ? () => {
                          setSelectedCapability(
                            "author.co_authorship"
                          );
                          setModal("analysis");
                        }
                      : undefined
                  }
                />

              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6">

                <SectionHeader
                  title="Dataset Intelligence"
                  description="Current research data"
                />

                {datasets.length === 0 ? (
                  <EmptyState
                    title="No datasets"
                    description="Upload a CSV or text dataset to start your scientometric analysis."
                    action="Upload Dataset"
                    onAction={() =>
                      setModal("upload")
                    }
                  />
                ) : (
                  <div className="mt-5 space-y-3">

                    {datasets
                      .slice(0, 5)
                      .map((dataset) => (
                        <div
                          key={dataset.id}
                          className="flex items-center justify-between rounded-xl border border-slate-200 p-4"
                        >

                          <div className="min-w-0">

                            <div className="truncate text-sm font-bold">
                              {dataset.name ||
                                "Unnamed Dataset"}
                            </div>

                            <div className="mt-1 text-xs text-slate-400">
                              {dataset.source ||
                                "Unknown source"}{" "}
                              ·{" "}
                              {formatNumber(
                                dataset.record_count
                              )}{" "}
                              records
                            </div>

                          </div>

                          <StatusBadge
                            status={
                              dataset.status ||
                              "available"
                            }
                          />

                        </div>
                      ))}

                  </div>
                )}

              </div>

            </section>

            <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6">

              <SectionHeader
                title="Recent Analyses"
                description="Latest analytical runs in this workspace"
              />

              {analyses.length === 0 ? (
                <EmptyState
                  title="No analyses yet"
                  description="Choose an analytical capability to create your first analysis."
                  action="Run Analysis"
                  onAction={openAnalysisModal}
                />
              ) : (
                <div className="mt-5 overflow-hidden rounded-xl border border-slate-200">

                  <div className="grid grid-cols-[1.7fr_1fr_1fr_1fr] border-b border-slate-200 bg-slate-50 px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">

                    <div>
                      Analysis
                    </div>

                    <div>
                      Dataset Version
                    </div>

                    <div>
                      Status
                    </div>

                    <div>
                      Created
                    </div>

                  </div>

                  {analyses
                    .slice(0, 8)
                    .map((analysis) => (

                      <button
                        type="button"
                        key={analysis.id}
                        onClick={() =>
                          loadAnalysisResult(
                            analysis
                          )
                        }
                        className="grid w-full grid-cols-[1.7fr_1fr_1fr_1fr] items-center border-b border-slate-100 px-4 py-4 text-left last:border-b-0 hover:bg-slate-50"
                      >

                        <div>

                          <div className="text-sm font-bold">
                            {analysis.name ||
                              capabilityLabel(
                                analysis.analysis_type ||
                                  analysis.capability_id
                              )}
                          </div>

                          <div className="mt-1 text-[10px] text-slate-400">
                            {analysis.analysis_type ||
                              analysis.capability_id ||
                              "—"}
                          </div>

                        </div>

                        <div className="truncate text-xs text-slate-500">
                          {analysis.dataset_version_id ||
                            "—"}
                        </div>

                        <div>
                          <StatusBadge
                            status={
                              analysis.status ||
                              "created"
                            }
                          />
                        </div>

                        <div className="text-xs text-slate-500">
                          {formatDate(
                            analysis.created_at
                          )}
                        </div>

                      </button>

                    ))}

                </div>
              )}

            </section>

            <AnalysisResultPanel
              analysis={selectedAnalysis}
            />

            <section className="mt-8 rounded-2xl border border-slate-200 bg-slate-950 p-7 text-white">

              <div className="max-w-2xl">

                <div className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500">
                  AI Research Intelligence
                </div>

                <h2 className="mt-3 text-2xl font-black">
                  From metrics to research insight.
                </h2>

                <p className="mt-3 text-sm leading-6 text-slate-400">
                  SciAI is designed to move beyond
                  descriptive statistics toward
                  comparative analysis, interpretation,
                  and AI-assisted research intelligence.
                </p>

              </div>

            </section>

          </div>
        </div>
      </div>

      {modal === "analysis" && (
        <Modal
          title="Run Analysis"
          onClose={() => setModal(null)}
        >

          <p className="text-sm text-slate-500">
            Select a dataset version and an
            available analytical capability.
          </p>

          <div className="mt-5">

            <label className="text-xs font-bold text-slate-600">
              Dataset
            </label>

            <select
              value={selectedDatasetId}
              onChange={(e) =>
                setSelectedDatasetId(
                  e.target.value
                )
              }
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-slate-950"
            >

              <option value="">
                Select a dataset
              </option>

              {datasets.map((d) => (
                <option
                  key={d.id}
                  value={d.id}
                >
                  {d.name ||
                    "Unnamed Dataset"}
                </option>
              ))}

            </select>

          </div>

          <div className="mt-4">

            <label className="text-xs font-bold text-slate-600">
              Dataset Version
            </label>

            <select
              value={selectedVersionId}
              onChange={(e) =>
                setSelectedVersionId(
                  e.target.value
                )
              }
              disabled={
                !selectedDatasetId ||
                versions.length === 0
              }
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none disabled:bg-slate-50 disabled:text-slate-400"
            >

              <option value="">
                {selectedDatasetId
                  ? versions.length
                    ? "Select a dataset version"
                    : "No versions available"
                  : "Select a dataset first"}
              </option>

              {versions.map((v) => (
                <option
                  key={v.id}
                  value={v.id}
                >
                  Version{" "}
                  {v.version ?? "—"}
                  {v.record_count !==
                  undefined
                    ? ` · ${formatNumber(
                        v.record_count
                      )} records`
                    : ""}
                </option>
              ))}

            </select>

            {selectedVersion && (
              <div className="mt-2 text-[10px] text-slate-400">
                Version ID:{" "}
                {selectedVersion.id}
              </div>
            )}

          </div>

          <div className="mt-5">

            <label className="text-xs font-bold text-slate-600">
              Analytical Capability
            </label>

            <div className="mt-2 space-y-2">

              {capabilities.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 p-5 text-sm text-slate-400">
                  No analytical capabilities
                  are currently available.
                </div>
              ) : (
                capabilities.map(
                  (capability) => {
                    const isSelected =
                      selectedCapability ===
                      capability.name;

                    const provider =
                      capability.providers?.find(
                        (x) =>
                          x.available !==
                          false
                      ) ||
                      capability.providers?.[0];

                    return (
                      <button
                        key={
                          capability.name
                        }
                        type="button"
                        onClick={() =>
                          selectCapability(
                            capability.name
                          )
                        }
                        className={`w-full rounded-xl border p-4 text-left transition ${
                          isSelected
                            ? "border-slate-950 bg-slate-950 text-white"
                            : "border-slate-200 bg-white hover:bg-slate-50"
                        }`}
                      >

                        <div className="flex items-start justify-between gap-4">

                          <div className="min-w-0">

                            <div className="text-sm font-bold">
                              {capabilityLabel(
                                capability.name
                              )}
                            </div>

                            <div
                              className={`mt-1 text-xs ${
                                isSelected
                                  ? "text-slate-400"
                                  : "text-slate-500"
                              }`}
                            >
                              Scientometric
                              analytical
                              capability
                            </div>

                            <div
                              className={`mt-2 break-all text-[10px] font-semibold ${
                                isSelected
                                  ? "text-slate-500"
                                  : "text-slate-400"
                              }`}
                            >
                              {capability.name}
                            </div>

                          </div>

                          {provider && (
                            <div
                              className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-bold ${
                                isSelected
                                  ? "bg-white/10 text-slate-300"
                                  : "bg-slate-100 text-slate-500"
                              }`}
                            >
                              {provider.name ||
                                provider.package ||
                                "Provider"}
                            </div>
                          )}

                        </div>

                      </button>
                    );
                  }
                )
              )}

            </div>

          </div>

          <div className="mt-6 rounded-xl bg-slate-50 p-4">

            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Selected Analysis
            </div>

            <div className="mt-2 text-sm font-bold">
              {capabilityLabel(
                selectedCapability
              )}
            </div>

            <div className="mt-1 text-xs text-slate-400">
              {selectedCapability ||
                "No capability selected"}
            </div>

          </div>

          <div className="mt-6 flex justify-end gap-3">

            <button
              type="button"
              onClick={() =>
                setModal(null)
              }
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={runAnalysis}
              disabled={
                running ||
                !selectedCapability ||
                !selectedVersionId
              }
              className="rounded-lg bg-slate-950 px-5 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {running
                ? "Running…"
                : "Run Analysis"}
            </button>

          </div>

        </Modal>
      )}

      {modal === "upload" && (
        <Modal
          title="Upload Dataset"
          onClose={() => setModal(null)}
        >

          <p className="text-sm text-slate-500">
            Upload a CSV or text dataset to
            your current research project.
          </p>

          <div className="mt-5 space-y-4">

            <div>

              <label className="text-xs font-bold text-slate-600">
                Dataset Name
              </label>

              <input
                value={datasetName}
                onChange={(e) =>
                  setDatasetName(
                    e.target.value
                  )
                }
                placeholder="e.g. Scopus 2025"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-950"
              />

            </div>

            <div>

              <label className="text-xs font-bold text-slate-600">
                Source
              </label>

              <select
                value={datasetSource}
                onChange={(e) =>
                  setDatasetSource(
                    e.target.value
                  )
                }
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-slate-950"
              >

                <option value="Scopus">
                  Scopus
                </option>

                <option value="Web of Science">
                  Web of Science
                </option>

                <option value="OpenAlex">
                  OpenAlex
                </option>

                <option value="PubMed">
                  PubMed
                </option>

                <option value="Crossref">
                  Crossref
                </option>

                <option value="Other">
                  Other
                </option>

              </select>

            </div>

            <div>

              <label className="text-xs font-bold text-slate-600">
                Dataset File
              </label>

              <input
                type="file"
                accept=".csv,.txt,.ciw"
                onChange={(e) =>
                  setDatasetFile(
                    e.target.files?.[0] ||
                      null
                  )
                }
                className="mt-2 block w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm"
              />

              {datasetFile && (
                <div className="mt-2 text-xs text-slate-400">
                  Selected:{" "}
                  {datasetFile.name}
                </div>
              )}

            </div>

          </div>

          <div className="mt-6 flex justify-end gap-3">

            <button
              type="button"
              onClick={() =>
                setModal(null)
              }
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={uploadDataset}
              disabled={
                uploading ||
                !datasetFile ||
                !datasetName.trim()
              }
              className="rounded-lg bg-slate-950 px-5 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading
                ? "Uploading…"
                : "Upload Dataset"}
            </button>

          </div>

        </Modal>
      )}

    </main>
  );
}

function AnalysisResultPanel({
  analysis,
}: {
  analysis: Analysis | null;
}) {
  if (!analysis) return null;

  const payload =
    extractResultPayload(
      analysis.result
    );

  const records = sortRecords(
    payload.records,
    analysis.analysis_type ||
      analysis.capability_id
  );

  const columns =
    recordColumns(records);

  return (
    <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6">

      <div className="flex items-start justify-between gap-4">

        <SectionHeader
          title={capabilityLabel(
            analysis.analysis_type ||
              analysis.capability_id
          )}
          description={`Analysis result · ${
            analysis.status ||
            "completed"
          }`}
        />

        <StatusBadge
          status={
            analysis.status ||
            "completed"
          }
        />

      </div>

      {payload.scalarEntries.length >
        0 && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

          {payload.scalarEntries.map(
            ([key, value]) => (
              <div
                key={key}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4"
              >

                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {key.replace(
                    /_/g,
                    " "
                  )}
                </div>

                <div className="mt-2 break-all text-xl font-black">
                  {displayValue(value)}
                </div>

              </div>
            )
          )}

        </div>
      )}

      {records.length > 0 ? (
        <div className="mt-5 overflow-x-auto rounded-xl border border-slate-200">

          <table className="min-w-full text-sm">

            <thead className="bg-slate-50">

              <tr>

                {columns.map(
                  (column) => (
                    <th
                      key={column}
                      className="whitespace-nowrap px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-400"
                    >
                      {column.replace(
                        /_/g,
                        " "
                      )}
                    </th>
                  )
                )}

              </tr>

            </thead>

            <tbody>

              {records.map(
                (record, index) => (
                  <tr
                    key={`${analysis.id}-${index}`}
                    className="border-t border-slate-100"
                  >

                    {columns.map(
                      (column) => (
                        <td
                          key={column}
                          className="whitespace-nowrap px-4 py-3 font-medium text-slate-700"
                        >
                          {displayValue(
                            record[column]
                          )}
                        </td>
                      )
                    )}

                  </tr>
                )
              )}

            </tbody>

          </table>

        </div>
      ) : payload.scalarEntries.length ===
        0 ? (
        <EmptyState
          title="No tabular result"
          description="The analysis completed, but no records were returned by the backend."
        />
      ) : null}

      {payload.metadata.length > 0 && (
        <details className="mt-4">

          <summary className="cursor-pointer text-xs font-bold text-slate-500">
            Technical result metadata
          </summary>

          <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300">
            {JSON.stringify(
              Object.fromEntries(
                payload.metadata
              ),
              null,
              2
            )}
          </pre>

        </details>
      )}

    </section>
  );
}

function SidebarItem({
  label,
  active = false,
}: {
  label: string;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={`w-full rounded-lg px-3 py-2.5 text-left text-sm font-semibold transition ${
        active
          ? "bg-slate-950 text-white"
          : "text-slate-500 hover:bg-slate-50 hover:text-slate-950"
      }`}
    >
      {label}
    </button>
  );
}

function MetricCard({
  label,
  value,
  description,
  loading,
}: {
  label: string;
  value: string;
  description: string;
  loading?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">

      <div className="text-xs font-semibold text-slate-400">
        {label}
      </div>

      <div className="mt-3 text-3xl font-black tracking-tight">
        {loading ? "…" : value}
      </div>

      <div className="mt-1 text-xs text-slate-400">
        {description}
      </div>

    </div>
  );
}

function SectionHeader({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div>

      <h2 className="text-base font-black">
        {title}
      </h2>

      <p className="mt-1 text-xs text-slate-400">
        {description}
      </p>

    </div>
  );
}

function Coverage({
  label,
  available,
}: {
  label: string;
  available: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-100 px-3 py-3">

      <span className="text-xs font-semibold text-slate-600">
        {label}
      </span>

      <span
        className={`rounded-full px-2 py-1 text-[9px] font-bold ${
          available
            ? "bg-slate-950 text-white"
            : "bg-slate-100 text-slate-400"
        }`}
      >
        {available
          ? "Available"
          : "Unavailable"}
      </span>

    </div>
  );
}

function QuickCard({
  title,
  description,
  available,
  onClick,
}: {
  title: string;
  description: string;
  available: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={!available}
      onClick={onClick}
      className={`rounded-2xl border bg-white p-5 text-left transition ${
        available
          ? "border-slate-200 hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-sm"
          : "cursor-not-allowed border-slate-200 opacity-50"
      }`}
    >

      <div className="flex items-center justify-between">

        <div className="text-sm font-black">
          {title}
        </div>

        <div className="text-slate-300">
          →
        </div>

      </div>

      <p className="mt-2 text-xs leading-5 text-slate-400">
        {description}
      </p>

      <div className="mt-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
        {available
          ? "Available"
          : "Unavailable"}
      </div>

    </button>
  );
}

function EmptyState({
  title,
  description,
  action,
  onAction,
}: {
  title: string;
  description: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="mt-5 flex min-h-[150px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6">

      <div className="max-w-sm text-center">

        <div className="text-sm font-bold">
          {title}
        </div>

        <div className="mt-2 text-xs leading-5 text-slate-400">
          {description}
        </div>

        {action &&
          onAction && (
            <button
              type="button"
              onClick={onAction}
              className="mt-4 rounded-lg bg-slate-950 px-4 py-2 text-xs font-bold text-white"
            >
              {action}
            </button>
          )}

      </div>

    </div>
  );
}

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const normalized =
    status.toLowerCase();

  const positive =
    normalized.includes("complete") ||
    normalized.includes("success") ||
    normalized.includes("available") ||
    normalized.includes("ready");

  const active =
    normalized.includes("running") ||
    normalized.includes("process") ||
    normalized.includes("queued");

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[9px] font-bold ${
        positive
          ? "bg-slate-950 text-white"
          : active
          ? "bg-slate-200 text-slate-700"
          : "bg-slate-100 text-slate-500"
      }`}
    >
      {status}
    </span>
  );
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">

      <div
        className="absolute inset-0"
        onClick={onClose}
      />

      <div className="relative z-10 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">

        <div className="flex items-center justify-between">

          <h2 className="text-lg font-black">
            {title}
          </h2>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-950"
          >
            ✕
          </button>

        </div>

        {children}

      </div>

    </div>
  );
}