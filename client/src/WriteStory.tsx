import React, { Component } from 'react';
import { Button, Col, Row } from 'react-bootstrap';
import TextareaAutosize from 'react-autosize-textarea';
import axios from 'axios';

interface Props {
    username: string,
}

interface State {
    prevLine?: string,
    prevAuthor?: string,
    currLine: string,
    currIndex?: number,
    maxLines?: number,
    error?: string,
}

export default class WriteStory extends Component<Props, State> {
    textarea: HTMLTextAreaElement | null;

    constructor(props: Props) {
        super(props);

        this.state = {
            currLine: ''
        }

        this.textarea = null;
    }

    getNewLine() {
        axios
            .post('/api/get_line', { 'user': this.props.username })
            .then(r => r.data)
            .then((data) => {
                if (!data.error) {
                    this.setState({ ...data });
                    this.textarea?.focus();
                } else {
                    this.setState({ error: data.error });
                }
            })
    }

    componentDidMount() {
        this.getNewLine();
    }

    buildButtonBar() {
        const showSubmit: boolean = Boolean(this.state.prevLine);
        const allowSubmit: boolean = Boolean(this.state.currLine);

        console.log(`allowSubmit: ${allowSubmit}`);
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
                        >
                            Submit!
                        </Button>
                        : null
                    }
                </Col>
            </Row>
        )
    }

    buildWriteBox() {
        let lastLine: boolean = false;
        if (this.state.currIndex && this.state.maxLines) {
            lastLine = (this.state.currIndex === this.state.maxLines);
        }

        if (!this.state.prevLine) {
            return null;
        }

        return (
            <div className="write-box">
                <div className="prev-story-container text-center">
                    <span>
                        {this.state.prevLine}
                    </span>
                    {
                        this.state.prevAuthor
                            ? <span className="author-attr">@{this.state.prevAuthor}</span>
                            : null
                    }
                </div>
                <div className="story-input-container">
                    <Row>
                        <Col>
                            <TextareaAutosize
                                className="story-input"
                                placeholder="> Continue the story..."
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
                { this.buildWriteBox() }
                { this.buildButtonBar() }
            </div>
        );
    }
}