import React from 'react';
import { motion } from 'framer-motion';

/**
 * 使用 Framer Motion 的高级动画组件
 * 提供更丰富的动画效果和更好的性能
 */

// 预设动画变体
const animationVariants = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  slideUp: {
    initial: { opacity: 0, y: 50 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 50 },
  },
  slideDown: {
    initial: { opacity: 0, y: -50 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -50 },
  },
  slideLeft: {
    initial: { opacity: 0, x: 50 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 50 },
  },
  slideRight: {
    initial: { opacity: 0, x: -50 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -50 },
  },
  scale: {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.8 },
  },
  rotate: {
    initial: { opacity: 0, rotate: -180 },
    animate: { opacity: 1, rotate: 0 },
    exit: { opacity: 0, rotate: 180 },
  },
  bounce: {
    initial: { opacity: 0, y: -50 },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 10,
      },
    },
    exit: { opacity: 0, y: -50 },
  },
};

/**
 * MotionAnimate 组件
 * @param {string} type - 动画类型
 * @param {number} duration - 动画持续时间（秒）
 * @param {number} delay - 动画延迟（秒）
 * @param {boolean} trigger - 是否显示
 * @param {object} customVariants - 自定义动画变体
 * @param {React.ReactNode} children - 子元素
 */
const MotionAnimate = ({
  type = 'fadeIn',
  duration = 0.5,
  delay = 0,
  trigger = true,
  customVariants,
  children,
  ...props
}) => {
  const variants = customVariants || animationVariants[type] || animationVariants.fadeIn;

  const transition = {
    duration,
    delay,
    ease: 'easeInOut',
  };

  if (!trigger) {
    return null;
  }

  return (
    <motion.div
      initial="initial"
      animate="animate"
      exit="exit"
      variants={variants}
      transition={transition}
      {...props}
    >
      {children}
    </motion.div>
  );
};

/**
 * 列表动画组件 - 用于动画化列表项
 */
export const MotionList = ({ children, stagger = 0.1, ...props }) => {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: stagger,
      },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" {...props}>
      {React.Children.map(children, (child, index) => (
        <motion.div key={index} variants={item}>
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
};

/**
 * 悬停动画组件
 */
export const MotionHover = ({ children, scale = 1.05, ...props }) => {
  return (
    <motion.div
      whileHover={{ scale }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

/**
 * 拖拽动画组件
 */
export const MotionDrag = ({ children, ...props }) => {
  return (
    <motion.div
      drag
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={0.2}
      whileDrag={{ scale: 1.1 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default MotionAnimate;
