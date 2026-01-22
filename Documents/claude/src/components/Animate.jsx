import React, { useEffect, useState } from 'react';
import './Animate.css';

/**
 * 基础动画组件
 * @param {string} type - 动画类型: 'fadeIn' | 'fadeOut' | 'slideInUp' | 'slideInDown' | 'slideInLeft' | 'slideInRight' | 'scaleIn' | 'scaleOut' | 'rotate' | 'bounce' | 'pulse' | 'shake'
 * @param {number} duration - 动画持续时间（秒）
 * @param {number} delay - 动画延迟时间（秒）
 * @param {boolean} trigger - 触发动画的布尔值
 * @param {string} className - 额外的CSS类名
 * @param {React.ReactNode} children - 子元素
 */
const Animate = ({
  type = 'fadeIn',
  duration = 0.5,
  delay = 0,
  trigger = true,
  className = '',
  children,
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(trigger);

  useEffect(() => {
    if (trigger) {
      setIsVisible(true);
    } else {
      setIsVisible(false);
    }
  }, [trigger]);

  const animationClass = `animate-${type}`;
  const customStyle = {
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`,
    ...props.style,
  };

  if (!isVisible && (type === 'fadeOut' || type === 'scaleOut')) {
    return null;
  }

  return (
    <div
      className={`${animationClass} ${className}`}
      style={customStyle}
      {...props}
    >
      {children}
    </div>
  );
};

export default Animate;
