import React, { Component } from 'react';
import { Button, Col, Row } from 'react-bootstrap';
import TextareaAutosize from 'react-autosize-textarea';

interface Props {
    username: string,
}

interface State {
    prevLine?: string,
    prevAuthor?: string,
    currLine: string,
}

export default class WriteStory extends Component<Props, State> {
    textarea: HTMLTextAreaElement | null;

    constructor(props: Props) {
        super(props);

        this.state = {
            currLine: '',
        }

        this.textarea = null;
    }

    componentDidMount() {
        this.textarea?.focus();
    }

    render() {
        return (
            <div className="write-container">
                <div className="write-box">
                    <div className="prev-story-container text-center">
                        <span>
                            Once upon a time, there was a miraculous unicorn
                            named Ruth Bader Ginsburg.
                        </span>
                        <span className="author-attr">@Parth</span>
                    </div>
                    <div className="story-input-container">
                        <Row>
                            {/* <Col className="story-prompt">
                            <span>&gt;</span>
                            </Col> */}
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
                            </Col>
                        </Row>
                    </div>
                </div>
                <Row className="mt-2">
                    <Col className="text-center">
                        <Button
                            className="new-story-btn"
                        >
                            Get a New Story
                        </Button>
                        <Button
                            variant="success"
                            className="submit-btn ml-3"
                        >
                            Submit!
                        </Button>
                    </Col>
                </Row>
            </div>
        );
    }
}