'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { HandRankings } from '../../components/tutorial/HandRankings';
import { BasicStrategy } from '../../components/tutorial/BasicStrategy';
import { AIDecisionGuide } from '../../components/tutorial/AIDecisionGuide';

export default function TutorialPage() {
  const [currentSection, setCurrentSection] = useState(0);

  const sections = [
    { id: 'rankings', title: 'Hand Rankings', component: <HandRankings /> },
    { id: 'strategy', title: 'Basic Strategy', component: <BasicStrategy /> },
    { id: 'ai', title: 'AI & SPR', component: <AIDecisionGuide /> },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-700 to-green-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-800">Texas Hold'em Tutorial</h1>
            <Link
              href="/"
              className="text-sm text-green-600 hover:text-green-700 font-medium"
            >
              ← Back to Home
            </Link>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-2 border-b border-gray-200">
            {sections.map((section, index) => (
              <button
                key={section.id}
                onClick={() => setCurrentSection(index)}
                className={`px-4 py-2 font-medium text-sm transition-colors relative ${
                  currentSection === index
                    ? 'text-green-700'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                {section.title}
                {currentSection === index && (
                  <motion.div
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-700"
                    layoutId="activeTab"
                  />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <motion.div
          key={currentSection}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="bg-white rounded-2xl shadow-2xl p-6 mb-6"
        >
          {sections[currentSection].component}
        </motion.div>

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center bg-white rounded-2xl shadow-2xl p-6">
          <button
            onClick={() => setCurrentSection(Math.max(0, currentSection - 1))}
            disabled={currentSection === 0}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            ← Previous
          </button>

          <div className="text-sm text-gray-600">
            Section {currentSection + 1} of {sections.length}
          </div>

          {currentSection < sections.length - 1 ? (
            <button
              onClick={() => setCurrentSection(Math.min(sections.length - 1, currentSection + 1))}
              className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
            >
              Next →
            </button>
          ) : (
            <Link
              href="/"
              className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
            >
              Start Playing →
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
