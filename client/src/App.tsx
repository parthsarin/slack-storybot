import React, { FunctionComponent, useState } from 'react';
import { Container } from 'react-bootstrap';
import './App.css';
import Authenticate from './Authenticate';
import WriteStory from './WriteStory';

const App: FunctionComponent<{}> = () => {
    // Get the slack name from local storage if it exists there
    const [slackName, setSlackName] = useState<string | null>(
        localStorage.getItem("slackName")
    );

    if (!slackName) {
        // Not authenticated yet
        return (
            <Authenticate
                onSubmit={
                    (newUsername) => {
                        setSlackName(newUsername);
                        localStorage.setItem('slackName', newUsername);
                    }
                }
                newUser={localStorage.getItem('slackName') === null}
            />
        );
    }

    // Authenticated
    return (
        <Container className="mt-2 mb-2">
            <h1>Hey, @{slackName}! 🖋</h1>
            <p className="lead">
                Not you?&nbsp;
                <button 
                    className="link-button" 
                    onClick={() => setSlackName('')}>
                    Re-authenticate here
                </button>.
            </p>

            <WriteStory
                username={slackName}
            />
        </Container>
    );
}

export default App;
