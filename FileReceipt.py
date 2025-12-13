# FileReceipt is licensed under the GNU General Public License v3.0.
# See the LICENSE.txt file in the project root for the full license text.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.

# Copyright (c) 2023 CrimLawTech LLC
# brian@crimlawtech.com

import sys
from PyQt5.QtWidgets import QApplication
from filereceipt.ui.main_window import MainWindow


if __name__ == '__main__':
    # Create a QApplication
    app = QApplication(sys.argv)
    
    # Set the global font
    font = QApplication.font()
    font.setFamily("Arial")
    font.setPointSize(10)
    QApplication.setFont(font)
    
    # Create a MainWindow
    window = MainWindow()
    # Show the MainWindow
    window.show()
    # Enter the QApplication's main event loop, and exit when it is done
    sys.exit(app.exec_())
