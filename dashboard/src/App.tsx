import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Briefcase, Clock, Activity } from 'lucide-react';
import './index.css';

interface Stats {
  jobs_applied: number;
  last_run: string | null;
}

function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch real-time data from the Express backend
    fetch('/api/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching stats:", err);
        setLoading(false);
      });
  }, []);

  const containerVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.8, ease: "easeOut", staggerChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5 } }
  };

  return (
    <motion.div 
      className="dashboard-container"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <div className="glass-card">
        <motion.div className="header" variants={itemVariants}>
          <h1>JobHunt Pro</h1>
          <p>لوحة التحكم المركزية - مستوى الوحش</p>
        </motion.div>

        {loading ? (
          <div style={{ textAlign: 'center', margin: '2rem 0' }}>
            <Activity className="stat-icon" size={48} style={{ animation: 'spin 2s linear infinite' }} />
            <p>جاري سحب البيانات الحية...</p>
          </div>
        ) : (
          <motion.div className="stats-grid" variants={containerVariants}>
            <motion.div className="stat-box" variants={itemVariants}>
              <Briefcase className="stat-icon" size={32} />
              <div className="stat-value">{stats?.jobs_applied || 0}</div>
              <div className="stat-label">إجمالي الوظائف المُقدم عليها</div>
            </motion.div>

            <motion.div className="stat-box" variants={itemVariants}>
              <Clock className="stat-icon" size={32} />
              <div className="stat-value" style={{ fontSize: '1.5rem', color: '#f8fafc' }}>
                {stats?.last_run || 'لم يتم التشغيل بعد'}
              </div>
              <div className="stat-label">آخر تحديث للنشاط</div>
            </motion.div>
          </motion.div>
        )}

        <motion.div className="footer" variants={itemVariants}>
          <div className="status-dot"></div>
          <span>الخادم متصل ويعمل بوضع التخفي (Always-On)</span>
        </motion.div>
      </div>
    </motion.div>
  );
}

export default App;
