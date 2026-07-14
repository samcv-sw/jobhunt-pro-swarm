import React from 'react';
import renderer from 'react-test-renderer';
import { SkeletonLoader, SkeletonProfile, SkeletonCard } from '../src/components/SkeletonLoader';

describe('SkeletonLoader Snapshots', () => {
  it('renders SkeletonLoader correctly', () => {
    const tree = renderer.create(<SkeletonLoader />).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('renders SkeletonProfile correctly', () => {
    const tree = renderer.create(<SkeletonProfile />).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('renders SkeletonCard correctly', () => {
    const tree = renderer.create(<SkeletonCard />).toJSON();
    expect(tree).toMatchSnapshot();
  });
});
