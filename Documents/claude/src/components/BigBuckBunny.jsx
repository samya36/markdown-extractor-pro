import React, { useState } from 'react';
import './BigBuckBunny.css';

/**
 * Big Buck Bunny 动画场景组件
 * 创建一个经典的Big Buck Bunny风格的动画场景
 */
const BigBuckBunny = ({ 
  autoPlay = true, 
  speed = 1,
  showControls = true 
}) => {
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [animationSpeed, setAnimationSpeed] = useState(speed);

  const toggleAnimation = () => {
    setIsPlaying(!isPlaying);
  };

  const resetAnimation = () => {
    setIsPlaying(false);
    setTimeout(() => {
      setIsPlaying(true);
    }, 100);
  };

  const sceneStyle = {
    '--animation-speed': animationSpeed,
  };

  const getAnimationStyle = (baseDuration) => ({
    animationDuration: `${baseDuration / animationSpeed}s`,
    animationPlayState: isPlaying ? 'running' : 'paused',
  });

  return (
    <div className="big-buck-container">
      <div 
        className="big-buck-scene" 
        style={sceneStyle}
      >
        {/* 太阳 */}
        <div className="sun" style={getAnimationStyle(20)}></div>

        {/* 云朵 */}
        <div className="cloud cloud1" style={getAnimationStyle(20)}></div>
        <div className="cloud cloud2" style={getAnimationStyle(20)}></div>
        <div className="cloud cloud3" style={getAnimationStyle(20)}></div>

        {/* 树木 */}
        <div className="tree tree1" style={getAnimationStyle(3)}>
          <div className="tree-trunk"></div>
          <div className="tree-crown"></div>
        </div>
        <div className="tree tree2" style={getAnimationStyle(3)}>
          <div className="tree-trunk"></div>
          <div className="tree-crown"></div>
        </div>
        <div className="tree tree3" style={getAnimationStyle(3)}>
          <div className="tree-trunk"></div>
          <div className="tree-crown"></div>
        </div>

        {/* 兔子 */}
        <div className="bunny" style={getAnimationStyle(2)}>
          <div className="bunny-head">
            <div className="bunny-ear bunny-ear-left">
              <div className="bunny-ear-inner"></div>
            </div>
            <div className="bunny-ear bunny-ear-right">
              <div className="bunny-ear-inner"></div>
            </div>
            <div className="bunny-eye bunny-eye-left"></div>
            <div className="bunny-eye bunny-eye-right"></div>
            <div className="bunny-nose"></div>
            <div className="bunny-mouth"></div>
          </div>
          <div className="bunny-body">
            <div className="bunny-arm bunny-arm-left"></div>
            <div className="bunny-arm bunny-arm-right"></div>
            <div className="bunny-leg bunny-leg-left"></div>
            <div className="bunny-leg bunny-leg-right"></div>
          </div>
        </div>

        {/* 胡萝卜 */}
        <div className="carrot" style={getAnimationStyle(1.5)}>
          <div className="carrot-top">
            <div className="carrot-leaf"></div>
            <div className="carrot-leaf"></div>
            <div className="carrot-leaf"></div>
          </div>
          <div className="carrot-body"></div>
        </div>

        {/* 蝴蝶 */}
        <div className="butterfly" style={getAnimationStyle(8)}>
          <div className="butterfly-body">
            <div 
              className="butterfly-wing butterfly-wing-left"
              style={getAnimationStyle(0.3)}
            ></div>
            <div 
              className="butterfly-wing butterfly-wing-right"
              style={getAnimationStyle(0.3)}
            ></div>
          </div>
        </div>
      </div>

      {showControls && (
        <div className="bunny-controls">
          <button onClick={toggleAnimation}>
            {isPlaying ? '⏸ 暂停' : '▶ 播放'}
          </button>
          <button onClick={resetAnimation}>🔄 重置</button>
          <button onClick={() => setAnimationSpeed(0.5)}>🐌 慢速</button>
          <button onClick={() => setAnimationSpeed(1)}>▶ 正常</button>
          <button onClick={() => setAnimationSpeed(2)}>⚡ 快速</button>
        </div>
      )}
    </div>
  );
};

export default BigBuckBunny;
