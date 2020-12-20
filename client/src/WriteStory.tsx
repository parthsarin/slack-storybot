import React, { Component } from 'react';
import { Col, Row } from 'react-bootstrap';
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
    constructor(props: Props) {
        super(props);

        this.state = {
            currLine: '',
        }
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
                            <Col className="story-prompt">
                            <span>&gt;</span>
                            </Col>
                            <Col>
                                <TextareaAutosize
                                    className="story-input"
                                    placeholder="Continue the story..."
                                    value={this.state.currLine}
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
            </div>
        );
    }
}