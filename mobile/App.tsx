import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, ActivityIndicator } from 'react-native';

export default function App() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching dashboard stats from our FastAPI backend
    setTimeout(() => {
      setData({
        active_jobs: 142,
        success_rate: "98.5%",
        status: "Healthy"
      });
      setLoading(false);
    }, 1000);
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>JobHunt Pro Dashboard</Text>
      </View>
      
      {loading ? (
        <ActivityIndicator size="large" color="#FFD700" />
      ) : (
        <View style={styles.statsContainer}>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>Active Scrapes</Text>
            <Text style={styles.statValue}>{data.active_jobs}</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>Success Rate</Text>
            <Text style={styles.statValue}>{data.success_rate}</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>System Status</Text>
            <Text style={[styles.statValue, { color: '#4CAF50' }]}>{data.status}</Text>
          </View>
        </View>
      )}
      <StatusBar style="light" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
    alignItems: 'center',
    paddingTop: 60,
  },
  header: {
    marginBottom: 40,
  },
  headerText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
  },
  statsContainer: {
    width: '90%',
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statBox: {
    backgroundColor: '#1E1E1E',
    width: '48%',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  statLabel: {
    color: '#888',
    fontSize: 14,
    marginBottom: 8,
  },
  statValue: {
    color: '#FFF',
    fontSize: 22,
    fontWeight: 'bold',
  },
});
