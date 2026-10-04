/**
 * Registers the Chart.js building blocks used across every dashboard
 * chart. Import this module (for its side effect) once before rendering
 * any chart -- individual chart components just import from
 * "react-chartjs-2" and assume registration already happened here.
 */
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

export const CHART_COLORS = {
  accent: "#3654FF",
  success: "#1B8A5A",
  warning: "#B7791F",
  danger: "#C4402B",
  muted: "#9CA3AF",
};

export const chartBaseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { font: { family: "Inter", size: 11 }, boxWidth: 10 } },
  },
};
