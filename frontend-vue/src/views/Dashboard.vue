<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>JobHunt Pro Analytics</h1>
      <p>Your job application statistics and success metrics</p>
    </header>

    <div v-if="loading" class="loading">Loading dashboard...</div>
    
    <div v-else class="dashboard-content">
      <div class="stats-cards">
        <div class="card">
          <h3>Total Applications</h3>
          <div class="value">{{ stats.totalApplications }}</div>
        </div>
        <div class="card">
          <h3>Interviews</h3>
          <div class="value">{{ stats.interviews }}</div>
        </div>
        <div class="card">
          <h3>Offers</h3>
          <div class="value">{{ stats.offers }}</div>
        </div>
        <div class="card">
          <h3>Success Rate</h3>
          <div class="value success">{{ stats.successRate }}</div>
        </div>
      </div>
      
      <div class="charts-container">
        <div ref="chartRef" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';

const loading = ref(true);
const stats = ref({
  totalApplications: 0,
  interviews: 0,
  offers: 0,
  successRate: '0%'
});
const chartRef = ref(null);
let chartInstance = null;

onMounted(async () => {
  try {
    // We connect to the Node.js API (Render)
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000';
    const response = await axios.get(`${apiUrl}/api/stats`);
    stats.value = response.data;
    loading.value = false;
    
    // Initialize Echarts
    setTimeout(() => {
      if (chartRef.value) {
        chartInstance = echarts.init(chartRef.value, 'dark');
        
        const option = {
          backgroundColor: 'transparent',
          title: {
            text: 'Application Funnel',
            textStyle: { color: '#c9d1d9' }
          },
          tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b} : {c}'
          },
          series: [
            {
              name: 'Funnel',
              type: 'funnel',
              left: '10%',
              top: 60,
              bottom: 60,
              width: '80%',
              min: 0,
              max: 200,
              minSize: '0%',
              maxSize: '100%',
              sort: 'descending',
              gap: 2,
              label: {
                show: true,
                position: 'inside'
              },
              labelLine: {
                length: 10,
                lineStyle: { width: 1, type: 'solid' }
              },
              itemStyle: {
                borderColor: '#fff',
                borderWidth: 1
              },
              emphasis: {
                label: { fontSize: 20 }
              },
              data: [
                { value: stats.value.totalApplications, name: 'Applied' },
                { value: stats.value.interviews, name: 'Interviews' },
                { value: stats.value.offers, name: 'Offers' }
              ]
            }
          ]
        };
        chartInstance.setOption(option);
      }
    }, 100);
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    loading.value = false;
  }
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
  }
});
</script>

<style scoped>
.dashboard-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 2rem;
  text-align: center;
}

.dashboard-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, #58a6ff, #8a2be2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.card {
  background: rgba(22, 27, 34, 0.8);
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  backdrop-filter: blur(10px);
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  border-color: #58a6ff;
}

.card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #8b949e;
}

.card .value {
  font-size: 2rem;
  font-weight: bold;
  color: #c9d1d9;
}

.card .value.success {
  color: #3fb950;
}

.charts-container {
  background: rgba(22, 27, 34, 0.8);
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 1.5rem;
  height: 500px;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
