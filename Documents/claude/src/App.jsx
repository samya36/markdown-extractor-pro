import React, { useState } from 'react';
import Animate from './components/Animate';
import MotionAnimate, { MotionList, MotionHover, MotionDrag } from './components/MotionAnimate';
import BigBuckBunny from './components/BigBuckBunny';
import BookVideoGenerator from './components/BookVideoGenerator';
import './App.css';

function App() {
  const [showBasic, setShowBasic] = useState(true);
  const [showMotion, setShowMotion] = useState(true);
  const [animationType, setAnimationType] = useState('fadeIn');

  return (
    <div className="app">
      <h1>动画组件示例</h1>

      {/* 书籍视频生成器 */}
      <section className="section">
        <BookVideoGenerator />
      </section>

      {/* Big Buck Bunny 经典动画 */}
      <section className="section">
        <h2>🐰 Big Buck Bunny 经典动画</h2>
        <p style={{ marginBottom: '20px', color: '#666' }}>
          一个经典的Big Buck Bunny风格动画场景，包含可爱的兔子、自然场景和生动的动画效果
        </p>
        <BigBuckBunny autoPlay={true} showControls={true} />
      </section>

      {/* 基础动画组件示例 */}
      <section className="section">
        <h2>基础动画组件（CSS动画）</h2>
        <div className="controls">
          <button onClick={() => setShowBasic(!showBasic)}>
            {showBasic ? '隐藏' : '显示'}
          </button>
        </div>
        <div className="examples">
          <Animate type="fadeIn" trigger={showBasic}>
            <div className="box">淡入动画</div>
          </Animate>
          <Animate type="slideInUp" trigger={showBasic} delay={0.1}>
            <div className="box">向上滑入</div>
          </Animate>
          <Animate type="slideInLeft" trigger={showBasic} delay={0.2}>
            <div className="box">从左滑入</div>
          </Animate>
          <Animate type="scaleIn" trigger={showBasic} delay={0.3}>
            <div className="box">缩放进入</div>
          </Animate>
          <Animate type="bounce" trigger={showBasic} delay={0.4}>
            <div className="box">弹跳动画</div>
          </Animate>
          <Animate type="pulse" trigger={showBasic} delay={0.5}>
            <div className="box">脉冲动画</div>
          </Animate>
        </div>
      </section>

      {/* Framer Motion 动画组件示例 */}
      <section className="section">
        <h2>Framer Motion 动画组件</h2>
        <div className="controls">
          <button onClick={() => setShowMotion(!showMotion)}>
            {showMotion ? '隐藏' : '显示'}
          </button>
          <select
            value={animationType}
            onChange={(e) => setAnimationType(e.target.value)}
          >
            <option value="fadeIn">淡入</option>
            <option value="slideUp">向上滑入</option>
            <option value="slideDown">向下滑入</option>
            <option value="slideLeft">向左滑入</option>
            <option value="slideRight">向右滑入</option>
            <option value="scale">缩放</option>
            <option value="rotate">旋转</option>
            <option value="bounce">弹跳</option>
          </select>
        </div>
        <div className="examples">
          <MotionAnimate type={animationType} trigger={showMotion}>
            <div className="box motion-box">Motion 动画</div>
          </MotionAnimate>
        </div>
      </section>

      {/* 列表动画示例 */}
      <section className="section">
        <h2>列表动画</h2>
        <MotionList stagger={0.1}>
          <div className="box">列表项 1</div>
          <div className="box">列表项 2</div>
          <div className="box">列表项 3</div>
          <div className="box">列表项 4</div>
          <div className="box">列表项 5</div>
        </MotionList>
      </section>

      {/* 悬停动画示例 */}
      <section className="section">
        <h2>悬停动画</h2>
        <div className="examples">
          <MotionHover scale={1.1}>
            <div className="box hover-box">悬停我试试</div>
          </MotionHover>
        </div>
      </section>

      {/* 拖拽动画示例 */}
      <section className="section">
        <h2>拖拽动画</h2>
        <div className="examples drag-container">
          <MotionDrag>
            <div className="box drag-box">拖拽我</div>
          </MotionDrag>
        </div>
      </section>
    </div>
  );
}

export default App;
