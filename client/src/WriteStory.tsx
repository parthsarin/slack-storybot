import React, { Component } from 'react';
import { Alert, Button, Col, Row, Spinner } from 'react-bootstrap';
import TextareaAutosize from 'react-autosize-textarea';
import axios from 'axios';
import { User } from './App';

interface Props {
    user: User,
}

interface State {
    storyId?: number,
    storyIdHistory: number[],
    writingNewStory?: boolean,

    prevLine?: string,
    prevAuthor?: User | null,

    currLine?: string,
    currIndex?: number,
    
    maxLines?: number,
    
    error?: string,
    loading: boolean,
}

export default class WriteStory extends Component<Props, State> {
    textarea: HTMLTextAreaElement | null;

    constructor(props: Props) {
        super(props);

        this.state = {
            storyIdHistory: [],
            currLine: '',
            loading: false,
        }

        this.textarea = null;

        this.submitLine = this.submitLine.bind(this);
        this.getNewLine = this.getNewLine.bind(this);
    }

    getNewLine() {
        this.setState({loading: true});
        axios
            .post('/api/get_line', { 
                username: this.props.user.username, 
                storyId: this.state.storyId,
                storyIdHistory: this.state.storyIdHistory
            })
            .then(r => r.data)
            .then((data) => {
                if (!data.error) {
                    // Append to history
                    let newHistory = [...this.state.storyIdHistory];
                    if (data.storyId !== undefined) {
                        newHistory.push(data.storyId);
                    }

                    // Inject data into state
                    this.setState({
                        ...data, 
                        currLine: '', // clear the textarea
                        storyIdHistory: newHistory 
                    });
                    this.textarea?.focus();
                } else {
                    this.setState({ error: data.error });
                }
            })
            .then(() => this.setState({loading: false}))
    }

    submitLine() {
        axios
            .post('/api/submit_line', {
                username: this.props.user.username,
                storyId: this.state.storyId,
                line: this.state.currLine
            })
            .then(r => r.data)
            .then((data) => {
                if (data.error) {
                    this.setState({ error: data.error })
                } else {
                    this.getNewLine();
                }
            })
    }

    onUnload = (e: BeforeUnloadEvent) => {
        axios
            .post('/api/release_story', {
                username: this.props.user.username,
                storyId: this.state.storyId
            })
    }

    componentDidMount() {
        this.getNewLine();
        window.addEventListener('beforeunload', this.onUnload);
    }

    componentWillUnmount() {
        window.removeEventListener('beforeunload', this.onUnload);
    }

    buildButtonBar() {
        const showSubmit: boolean = Boolean(
            this.state.prevLine || this.state.writingNewStory
        );
        const allowSubmit: boolean = Boolean(this.state.currLine);

        return (
            <Row className="mt-2">
                <Col className="text-center">
                    <Button
                        className="new-story-btn"
                        onClick={() => this.getNewLine()}
                    >
                        Get a New Story
                    </Button>
                    {
                        showSubmit
                        ? <Button
                            variant="success"
                            className="submit-btn ml-3"
                            disabled={!allowSubmit}
                            onClick={() => this.submitLine()}
                        >
                            Submit!
                        </Button>
                        : null
                    }
                </Col>
            </Row>
        )
    }

    buildPrompt() {
        if (!this.state.prevLine) {
            return null;
        }

        if (!this.state.prevAuthor) {
            return (
                <div className="prev-story-container">
                    <span>
                        {this.state.prevLine}
                    </span>
                </div>
            )
        }

        return (
            <div className="prev-story-container">
                <Row>
                    <Col md={10}>
                        <span>
                            {this.state.prevLine}
                        </span>
                    </Col>
                    <Col md={2}>
                        {
                            this.state.prevAuthor.profile_image
                            ? <img
                                src={this.state.prevAuthor.profile_image}
                                alt=""
                                className="rounded mr-0 ml-auto"
                                style={{
                                    display: 'block',
                                    width: '100px'
                                }}
                            />
                            : null
                        }
                        
                        <span className="author-attr">
                            {this.state.prevAuthor.first_name} {this.state.prevAuthor.last_name} (@{this.state.prevAuthor.username})
                        </span>
                    </Col>
                </Row>
            </div>
        )
    }

    buildWriteBox() {
        let lastLine: boolean = false;
        if (this.state.currIndex && this.state.maxLines) {
            lastLine = (this.state.currIndex === this.state.maxLines);
        }

        if (this.state.loading) {
            return (
                <div className="write-box text-center">
                    <Spinner animation='border' />
                    <h2 
                        className="h2 d-inline ml-4 loading-header"
                    >Loading...</h2>
                </div>
            )
        }

        if (!this.state.prevLine && !this.state.writingNewStory) {
            return null;
        }

        return (
            <div className="write-box">
                { this.buildPrompt() }
                <div className="story-input-container">
                    <Row>
                        <Col>
                            <TextareaAutosize
                                className="story-input"
                                placeholder={
                                    this.state.writingNewStory
                                    ? "> Start a new story..."
                                    : "> Continue the story..."
                                }
                                value={this.state.currLine}
                                ref={(r) => this.textarea = r}
                                onChange={(e) => {
                                    const ev = e.target as HTMLInputElement;

                                    this.setState({
                                        currLine: ev.value
                                    })
                                }}
                            />
                            {
                                this.state.currIndex
                                    ? <span className="story-progress">
                                        Line {this.state.currIndex} {
                                            this.state.maxLines
                                                ? `of ${this.state.maxLines}`
                                                : null
                                        }
                                    </span>
                                    : null
                            }
                            {
                                lastLine
                                    ? <span className="story-progress-warn">
                                        This is the last line!
                                    </span>
                                    : null
                            }
                        </Col>
                    </Row>
                </div>
            </div>
        );
    }

    render() {
        return (
            <div className="write-container">
                {
                    this.state.error
                    ? <Alert variant='danger'>
                        <b>Something went wrong</b>: { this.state.error }
                    </Alert>
                    : null
                }
                { this.buildWriteBox() }
                { this.buildButtonBar() }
            </div>
        );
    }
}