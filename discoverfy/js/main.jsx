import React from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import InfiniteScroll from 'react-infinite-scroll-component';
import PostParent from './posts';


class Feed extends React.Component {
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = { posts: [], next: '', url: '' };
    this.fetchData = this.fetchData.bind(this);
  }

  componentWillMount() {
    const type = performance.navigation.type;
    if (type === 2) {
      // read from history
      this.setState({
        posts: history.state.posts,
        next: history.state.next,
        url: history.state.url,
      });
    } else {
      // Call REST API to get posts
      fetch(this.props.url, { credentials: 'same-origin' })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then((data) => {
          this.setState({
            posts: data.results,
            next: data.next,
            url: data.url,
          });
          history.pushState(this.state, '', '/');
        })
        .catch(error => console.log(error)); // eslint-disable-line no-console
    }
  }

  fetchData() {
    fetch(this.state.next, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        const newResults = this.state.posts;
        data.results.forEach((result) => {
          newResults.push(result);
        });
        this.setState({
          posts: newResults,
          next: data.next,
          url: data.url,
        });
        history.pushState(this.state, '', '/');
      })
      .catch(error => console.log(error)); // eslint-disable-line no-console

    return this.state.next;
  }

  render() {
    return (
      <InfiniteScroll
        next={this.fetchData}
        hasMore={this.state.next !== ''}
      >
        <span>
          {this.state.posts.map(post =>
            (<PostParent
              postid={post.postid}
              url={post.url}
              key={post.postid}
            />),
          )}
        </span>
      </InfiniteScroll>
    );
  }
}

Feed.propTypes = {
  url: PropTypes.string.isRequired,
};

ReactDOM.render(
  <Feed url="/api/v1/p/" />,
  document.getElementById('posts'),
);
