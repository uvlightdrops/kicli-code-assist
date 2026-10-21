import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface Feature {
  id: string;
  label: string;
  icon: string;
  description: string;
}

interface FeatureNavProps {
  currentFeature: string;
  onFeatureChange: (featureId: string) => void;
}

const FEATURES: Feature[] = [
  {
    id: 'explain',
    label: 'Explain',
    icon: '📖',
    description: 'Understand code structure and logic',
  },
  {
    id: 'reasoning',
    label: 'Reasoning',
    icon: '🧠',
    description: 'Multi-step thinking about code improvements',
  },
  {
    id: 'ensemble',
    label: 'Ensemble',
    icon: '🎯',
    description: 'OpenAI + Ollama consensus voting',
  },
  {
    id: 'tools',
    label: 'Tools',
    icon: '⚙️',
    description: 'Feature settings and configurations',
  },
];

export function FeatureNav({ currentFeature, onFeatureChange }: FeatureNavProps) {
  const [isOpen, setIsOpen] = useState(false);
  const current = FEATURES.find(f => f.id === currentFeature);

  return (
    <div className="relative">
      {/* Desktop: Horizontal tabs */}
      <div className="hidden sm:flex gap-2 items-center">
        {FEATURES.map(feature => (
          <button
            key={feature.id}
            onClick={() => onFeatureChange(feature.id)}
            className={`px-3 py-2 rounded-lg transition-all flex items-center gap-2 text-sm font-medium ${
              currentFeature === feature.id
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-700 text-gray-200 hover:bg-gray-600'
            }`}
            title={feature.description}
          >
            <span>{feature.icon}</span>
            <span>{feature.label}</span>
          </button>
        ))}
      </div>

      {/* Mobile: Dropdown */}
      <div className="sm:hidden">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 bg-gray-700 text-gray-200 rounded-lg hover:bg-gray-600 transition-all text-sm font-medium w-full justify-between"
        >
          <span className="flex items-center gap-2">
            <span>{current?.icon}</span>
            <span>{current?.label}</span>
          </span>
          <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute top-full mt-2 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50">
            {FEATURES.map(feature => (
              <button
                key={feature.id}
                onClick={() => {
                  onFeatureChange(feature.id);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-4 py-2 transition-all first:rounded-t-lg last:rounded-b-lg flex items-center gap-3 ${
                  currentFeature === feature.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-200 hover:bg-gray-700'
                }`}
              >
                <span>{feature.icon}</span>
                <div>
                  <div className="font-medium text-sm">{feature.label}</div>
                  <div className="text-xs opacity-75">{feature.description}</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
